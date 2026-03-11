"""Moteur de simulation event-driven pour uplinks périodiques."""

from __future__ import annotations

from dataclasses import dataclass, field
import heapq
import json
import logging
from pathlib import Path
import random
from time import monotonic
from typing import Any, Callable

from .io import write_run_outputs
from .adr.adr_legacy import AdrLegacyConfig, recommend_sf
from .adr.adr_mixra import AdrMixRaConfig, adapt_link
from .mab.ucb import UCB1
from .mab.ucb_forget import UCBForget
from .interference import InterferenceConfig, dbm_to_mw, mw_to_db, snr_db as compute_snr_db, transmission_success


@dataclass
class Node:
    node_id: int
    period_s: float
    next_uplink_s: float = 0.0
    payload_size: int = 12
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass(order=True)
class Event:
    time_s: float
    kind: str
    node_id: int
    sf: int = 7
    snr_db: float = 0.0
    sinr_db: float = 0.0
    threshold_db: float = 0.0
    success: bool = False
    delivered: bool = False
    payload_bytes: int = 0
    airtime_s: float = 0.0
    outage: bool = True
    switch_count: int = 0


@dataclass
class SimulationResult:
    uplink_count: int = 0
    events: list[Event] = field(default_factory=list)


class EventDrivenEngine:
    """Boucle event-driven basée sur une file de priorité.

    Chaque nœud planifie un événement ``uplink`` périodique.
    """

    def __init__(self, *, seed: int | None = None) -> None:
        self.rng = random.Random(seed)

    @staticmethod
    def _airtime_s(*, sf: int, payload_size: int) -> float:
        sf_factor = 2 ** max(sf - 7, 0)
        payload_factor = 1.0 + (max(payload_size, 1) / 12.0)
        return 0.015 * sf_factor * payload_factor

    def _compute_channel_state(
        self,
        *,
        node_count: int,
        mode: str,
        interference_db: float,
        sigma: float,
    ) -> tuple[float, float]:
        del mode, interference_db, sigma
        snr_base = 13.0 - 0.06 * node_count
        snr_db = snr_base + self.rng.uniform(-1.5, 1.5)
        return snr_db, snr_db

    def _derive_interferers(
        self,
        *,
        node_count: int,
        interference_db: float,
        sigma: float,
        signal_dbm: float,
        sf: int,
        cfg: InterferenceConfig,
    ) -> list[tuple[float, int]]:
        if not cfg.snir_enabled:
            return []

        dynamic_interference_db = max(0.0, interference_db + (0.03 * node_count) + 2.0 + abs(self.rng.gauss(0.0, sigma)))
        signal_mw = dbm_to_mw(signal_dbm)
        noise_mw = dbm_to_mw(cfg.noise_floor_dbm)
        snr_db = compute_snr_db(signal_dbm, cfg.noise_floor_dbm)
        target_sinr_db = snr_db - dynamic_interference_db
        target_denom_mw = signal_mw / (10.0 ** (target_sinr_db / 10.0))
        interf_mw = max(target_denom_mw - noise_mw, 0.0)
        if interf_mw <= 0.0:
            return []
        return [(mw_to_db(interf_mw), sf)]

    def _schedule_initial_events(self, nodes: list[Node]) -> list[Event]:
        queue: list[Event] = []
        for node in nodes:
            jitter = self.rng.uniform(0.0, min(node.period_s, 1.0))
            node.next_uplink_s = max(0.0, jitter)
            heapq.heappush(queue, Event(time_s=node.next_uplink_s, kind="uplink", node_id=node.node_id))
        return queue

    def _select_next_sf(
        self,
        *,
        algo_name: str,
        current_sf: int,
        snr_db: float,
        success: bool,
        airtime_s: float,
        node_id: int,
        adr_cfg: AdrLegacyConfig,
        adr_mixra_cfg: AdrMixRaConfig,
        mab_agents: dict[int, UCB1 | UCBForget],
        sf_arms: list[int],
        node_tx_power_dbm: float,
    ) -> int:
        """Calcule le SF cible via une interface commune, quel que soit l'algo."""

        if algo_name == "adr":
            return recommend_sf(current_sf=current_sf, snr_db=snr_db, cfg=adr_cfg)
        if algo_name == "adr_mixra":
            sf, _ = adapt_link(
                current_sf=current_sf,
                current_tx_power_dbm=node_tx_power_dbm,
                snr_db=snr_db,
                pdr_estimate=1.0 if success else 0.0,
                latency_estimate_s=airtime_s,
                cfg=adr_mixra_cfg,
            )
            return sf
        if algo_name in {"ucb", "ucb_forget"}:
            agent = mab_agents[node_id]
            arm = agent.select_arm()
            new_sf = sf_arms[arm]
            reward = (1.0 if success else -0.25) - 0.08 * airtime_s
            agent.update(arm, reward)
            return new_sf
        return current_sf

    def run(
        self,
        *,
        nodes: list[Node],
        until_s: float,
        mode: str = "snir_off",
        algo: str = "adr",
        interference_db: float = 0.0,
        sigma: float = 0.0,
        progress_callback: Callable[[float], None] | None = None,
    ) -> SimulationResult:
        if until_s <= 0:
            return SimulationResult()

        node_by_id = {n.node_id: n for n in nodes}
        node_count = len(nodes)
        algo_name = algo.lower()
        mode_name = mode.lower()
        adr_cfg = AdrLegacyConfig()
        adr_mixra_cfg = AdrMixRaConfig()
        interference_cfg = InterferenceConfig(snir_enabled=mode_name == "snir_on")

        mab_agents: dict[int, UCB1 | UCBForget] = {}
        sf_arms = [7, 8, 9, 10, 11, 12]
        for node in nodes:
            node.meta.setdefault("sf", self.rng.randint(8, 11))
            node.meta.setdefault("sf_previous", int(node.meta.get("sf", 7)))
            node.meta.setdefault("tx_power_dbm", 14.0)
            node.meta.setdefault("switch_count", 0)
            if algo_name == "ucb":
                mab_agents[node.node_id] = UCB1(n_arms=len(sf_arms))
            elif algo_name == "ucb_forget":
                mab_agents[node.node_id] = UCBForget(n_arms=len(sf_arms))

        queue = self._schedule_initial_events(nodes)
        result = SimulationResult()
        while queue:
            event = heapq.heappop(queue)
            if event.time_s > until_s:
                break

            if progress_callback is not None:
                progress_callback(min(max(event.time_s / until_s, 0.0), 1.0))

            if event.kind == "uplink":
                result.uplink_count += 1
                node = node_by_id[event.node_id]

                current_sf = int(node.meta.get("sf", 7))
                sf_previous = int(node.meta.get("sf_previous", current_sf))
                snr_db, sinr_db = self._compute_channel_state(
                    node_count=node_count,
                    mode=mode_name,
                    interference_db=interference_db,
                    sigma=sigma,
                )
                airtime_s = self._airtime_s(sf=current_sf, payload_size=node.payload_size)
                signal_dbm = interference_cfg.noise_floor_dbm + snr_db
                interferers = self._derive_interferers(
                    node_count=node_count,
                    interference_db=interference_db,
                    sigma=sigma,
                    signal_dbm=signal_dbm,
                    sf=current_sf,
                    cfg=interference_cfg,
                )
                success, metric_db = transmission_success(
                    signal_dbm,
                    signal_sf=current_sf,
                    interferers=interferers,
                    cfg=interference_cfg,
                )
                snr_db = compute_snr_db(signal_dbm, interference_cfg.noise_floor_dbm)
                sinr_db = metric_db if interference_cfg.snir_enabled else snr_db
                threshold_db = float(interference_cfg.snr_thresholds_db.get(current_sf, -20.0))

                new_sf = self._select_next_sf(
                    algo_name=algo_name,
                    current_sf=current_sf,
                    snr_db=snr_db,
                    success=success,
                    airtime_s=airtime_s,
                    node_id=node.node_id,
                    adr_cfg=adr_cfg,
                    adr_mixra_cfg=adr_mixra_cfg,
                    mab_agents=mab_agents,
                    sf_arms=sf_arms,
                    node_tx_power_dbm=float(node.meta.get("tx_power_dbm", 14.0)),
                )

                switched = int(new_sf != sf_previous)
                if switched:
                    node.meta["switch_count"] = int(node.meta.get("switch_count", 0)) + 1
                node.meta["sf"] = new_sf
                node.meta["sf_previous"] = new_sf

                result.events.append(
                    Event(
                        time_s=event.time_s,
                        kind="uplink",
                        node_id=node.node_id,
                        sf=current_sf,
                        snr_db=snr_db,
                        sinr_db=sinr_db,
                        threshold_db=threshold_db,
                        success=success,
                        delivered=success,
                        payload_bytes=node.payload_size,
                        airtime_s=airtime_s,
                        outage=not success,
                        switch_count=switched,
                    )
                )

                next_time = event.time_s + max(node.period_s, 1e-6)
                node.next_uplink_s = next_time
                heapq.heappush(queue, Event(time_s=next_time, kind="uplink", node_id=node.node_id))

        if progress_callback is not None:
            progress_callback(1.0)

        return result


@dataclass
class RunExecutionReport:
    run_id: str
    success: bool
    run_dir: Path
    error: str | None = None


@dataclass
class BatchExecutionReport:
    reports: list[RunExecutionReport]
    total_jobs: int = 0
    skipped_runs: int = 0
    scheduled_runs: int = 0
    interrupted: bool = False

    @property
    def failed_reports(self) -> list[RunExecutionReport]:
        return [report for report in self.reports if not report.success]


class GridRunOrchestrator:
    """Orchestre l'exécution d'une grille de runs et la persistance des artefacts."""

    def __init__(self, *, output_root: Path) -> None:
        self.output_root = output_root

    def _build_nodes(self, params: dict[str, Any]) -> list[Node]:
        node_count = int(params["N"])
        period_s = float(params.get("period_s", 60.0))
        payload_size = int(params.get("payload_size", 12))
        return [
            Node(node_id=node_id, period_s=period_s, payload_size=payload_size)
            for node_id in range(1, node_count + 1)
        ]

    def _build_run_config(self, params: dict[str, Any]) -> dict[str, Any]:
        return {
            "N": int(params["N"]),
            "speed": float(params.get("speed", 0.0)),
            "mobility_model": str(params.get("model", "RWP")).lower(),
            "mode": str(params.get("mode", "SNIR_OFF")).lower(),
            "algo": str(params.get("algo", "ADR")).lower(),
            "gateways": int(params.get("gateways", 1)),
            "sigma": float(params.get("sigma", 0.0)),
            "seed": int(params.get("seed", 0)),
            "rep": int(params.get("rep", 1)),
            **params,
        }

    def _logger_for_run(
        self,
        run_id: str,
    ) -> tuple[logging.Logger, list[logging.Handler], Path]:
        run_dir = self.output_root / "results" / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        logger = logging.getLogger(f"mobilesfrdth.run.{run_id}")
        logger.setLevel(logging.INFO)
        logger.propagate = False
        for handler in list(logger.handlers):
            logger.removeHandler(handler)
            handler.close()
        log_path = run_dir / "run.log"
        file_handler = logging.FileHandler(log_path, mode="w", encoding="utf-8")
        file_handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter("%(levelname)s | %(message)s"))
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        return logger, [file_handler, console_handler], run_dir


    def _log_sinr_success_diagnostic(
        self,
        *,
        logger: logging.Logger,
        run_id: str,
        events: list[Event],
        mode: str,
    ) -> None:
        if mode != "snir_on":
            logger.info("Diagnostic SINR->success ignoré: mode=%s", mode)
            return

        uplinks = [event for event in events if event.kind == "uplink"]
        if not uplinks:
            logger.info("Diagnostic SINR->success: aucun uplink")
            return

        bin_size_db = 2.0
        bins: dict[int, dict[str, int]] = {}
        for event in uplinks:
            bin_id = int(event.sinr_db // bin_size_db)
            slot = bins.setdefault(bin_id, {"total": 0, "success": 0})
            slot["total"] += 1
            slot["success"] += int(event.success)

        ordered = sorted(bins.items(), key=lambda item: item[0])
        rates = [(bin_id, values["success"] / max(values["total"], 1), values["total"]) for bin_id, values in ordered]
        inversions = 0
        for idx in range(1, len(rates)):
            if rates[idx][1] + 1e-9 < rates[idx - 1][1]:
                inversions += 1

        global_success = sum(int(event.success) for event in uplinks) / max(len(uplinks), 1)
        logger.info(
            "Diagnostic SINR->success run_id=%s: uplinks=%s, bins=%s, success_global=%.3f, inversions=%s",
            run_id,
            len(uplinks),
            len(rates),
            global_success,
            inversions,
        )
        for bin_id, rate, count in rates:
            lower = bin_id * bin_size_db
            upper = lower + bin_size_db
            logger.info("Diagnostic SINR bin [%.1f, %.1f) dB: p_success=%.3f (n=%s)", lower, upper, rate, count)

    def _is_run_completed(self, run_id: str) -> bool:
        run_dir = self.output_root / "results" / run_id
        required = [
            run_dir / "run_config.json",
            run_dir / "events.csv",
            run_dir / "node_timeseries.csv",
            run_dir / "summary.csv",
        ]
        return all(path.is_file() for path in required)

    def _write_campaign_progress(
        self,
        *,
        progress_path: Path,
        total_runs: int,
        completed_runs: int,
        skipped_runs: int,
        error_reports: list[RunExecutionReport],
        status: str,
    ) -> None:
        payload = {
            "status": status,
            "total_runs": total_runs,
            "runs_completed": completed_runs,
            "runs_skipped": skipped_runs,
            "runs_remaining": max(total_runs - completed_runs - skipped_runs, 0),
            "errors_count": len(error_reports),
            "errors": [
                {
                    "run_id": report.run_id,
                    "run_dir": str(report.run_dir),
                    "error": report.error,
                }
                for report in error_reports
            ],
        }
        progress_path.parent.mkdir(parents=True, exist_ok=True)
        progress_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    def execute_jobs(
        self,
        jobs: list[dict[str, Any]],
        *,
        resume: bool = False,
        max_runs: int | None = None,
        max_walltime_s: float | None = None,
        progress_path: Path | None = None,
        progress_interval_s: float = 30.0,
        on_run_complete: Callable[[RunExecutionReport, int, int, int, int, float | None], None] | None = None,
    ) -> BatchExecutionReport:
        if max_runs is not None and max_runs < 1:
            raise ValueError("max_runs doit être >= 1")
        if max_walltime_s is not None and max_walltime_s <= 0:
            raise ValueError("max_walltime_s doit être > 0")
        if progress_interval_s <= 0:
            raise ValueError("progress_interval_s doit être > 0")

        reports: list[RunExecutionReport] = []
        pending_jobs: list[dict[str, Any]] = []
        skipped_runs = 0

        for job in jobs:
            params = dict(job.get("params", {}))
            run_id = str(params.get("run_id", job.get("job_id", "run")))
            if resume and self._is_run_completed(run_id):
                skipped_runs += 1
                continue
            pending_jobs.append(job)

        if max_runs is not None:
            pending_jobs = pending_jobs[:max_runs]

        total_runs = len(jobs)
        walltime_start_s = monotonic()
        progress_target = progress_path or (self.output_root / "campaign_progress.json")
        scheduled_runs = len(pending_jobs)
        interrupted = False
        self._write_campaign_progress(
            progress_path=progress_target,
            total_runs=total_runs,
            completed_runs=0,
            skipped_runs=skipped_runs,
            error_reports=[],
            status="running",
        )

        for job in pending_jobs:
            params = dict(job.get("params", {}))
            run_id = str(params.get("run_id", job.get("job_id", "run")))
            logger, handlers, run_dir = self._logger_for_run(run_id)
            run_started_at_s = monotonic()
            run_success = False
            run_recorded = False
            try:
                elapsed_walltime_s = monotonic() - walltime_start_s
                if max_walltime_s is not None and elapsed_walltime_s >= max_walltime_s:
                    logger.warning(
                        "Arrêt campagne: plafond walltime atteint (%.1fs/%.1fs).",
                        elapsed_walltime_s,
                        max_walltime_s,
                    )
                    break

                seed = int(params.get("seed", 0))
                duration_s = float(params.get("duration_s", 3600.0))
                logger.info("Démarrage run_id=%s seed=%s", run_id, seed)
                logger.info("Paramètres: %s", params)

                engine = EventDrivenEngine(seed=seed)
                nodes = self._build_nodes(params)
                next_progress_log_at = monotonic() + progress_interval_s

                def _progress(progress: float) -> None:
                    nonlocal next_progress_log_at
                    now = monotonic()
                    if now >= next_progress_log_at:
                        next_progress_log_at = now + progress_interval_s
                        logger.info(
                            "Progression périodique run_id=%s: %s%%",
                            run_id,
                            int(progress * 100),
                        )

                result = engine.run(
                    nodes=nodes,
                    until_s=duration_s,
                    mode=str(params.get("mode", "snir_off")),
                    algo=str(params.get("algo", "adr")),
                    interference_db=float(params.get("interference_db", params.get("interference", 0.0))),
                    sigma=float(params.get("sigma", 0.0)),
                    progress_callback=_progress,
                )
                run_config = self._build_run_config(params)
                write_run_outputs(
                    output_root=self.output_root,
                    run_id=run_id,
                    run_config=run_config,
                    events=result.events,
                    duration_s=duration_s,
                    time_bin_s=float(params.get("time_bin_s", 10.0)),
                )
                self._log_sinr_success_diagnostic(
                    logger=logger,
                    run_id=run_id,
                    events=result.events,
                    mode=str(params.get("mode", "snir_off")).lower(),
                )
                logger.info("Run terminé: uplinks=%s", result.uplink_count)
                reports.append(RunExecutionReport(run_id=run_id, success=True, run_dir=run_dir))
                run_success = True
                run_recorded = True
            except KeyboardInterrupt:
                logger.warning("Interruption utilisateur détectée (Ctrl+C). Arrêt propre après ce run.")
                reports.append(
                    RunExecutionReport(
                        run_id=run_id,
                        success=False,
                        run_dir=run_dir,
                        error="Interruption utilisateur (Ctrl+C)",
                    )
                )
                run_recorded = True
                interrupted = True
            except Exception as exc:
                logger.exception("Run en erreur: %s", exc)
                reports.append(RunExecutionReport(run_id=run_id, success=False, run_dir=run_dir, error=str(exc)))
                run_recorded = True
            finally:
                if run_recorded:
                    run_duration_s = monotonic() - run_started_at_s
                    run_label = len(reports)
                    run_status = "succès" if run_success else "échec"
                    print(f"Run {run_label}/{scheduled_runs} | durée={run_duration_s:.2f}s | {run_status}")
                for handler in handlers:
                    logger.removeHandler(handler)
                    handler.close()

            run_index = len(reports)
            if on_run_complete is not None:
                elapsed_s = monotonic() - walltime_start_s
                remaining_runs = max(scheduled_runs - run_index, 0)
                eta_s = None
                if run_index > 0 and remaining_runs > 0:
                    eta_s = (elapsed_s / run_index) * remaining_runs
                last_report = reports[-1]
                on_run_complete(
                    last_report,
                    run_index,
                    scheduled_runs,
                    len([report for report in reports if report.success]),
                    len([report for report in reports if not report.success]),
                    eta_s,
                )

            self._write_campaign_progress(
                progress_path=progress_target,
                total_runs=total_runs,
                completed_runs=len([report for report in reports if report.success]),
                skipped_runs=skipped_runs,
                error_reports=[report for report in reports if not report.success],
                status="interrupted" if interrupted else "running",
            )

            if interrupted:
                break

        self._write_campaign_progress(
            progress_path=progress_target,
            total_runs=total_runs,
            completed_runs=len([report for report in reports if report.success]),
            skipped_runs=skipped_runs,
            error_reports=[report for report in reports if not report.success],
            status="interrupted" if interrupted else "finished",
        )

        return BatchExecutionReport(
            reports=reports,
            total_jobs=total_runs,
            skipped_runs=skipped_runs,
            scheduled_runs=scheduled_runs,
            interrupted=interrupted,
        )
