"""Moteur de simulation event-driven pour uplinks périodiques."""

from __future__ import annotations

from dataclasses import dataclass, field
import heapq
import json
import logging
import math
from pathlib import Path
import random
from time import monotonic
from typing import Any, Callable

from .io import write_run_outputs
from .adr.adr_legacy import AdrLegacyConfig, recommend_sf_with_reason
from .adr.adr_mixra import AdrMixRaConfig, adapt_link
from .channel import ChannelConfig, received_power_dbm
from .mab.ucb import UCB1
from .mab.ucb_forget import UCBForget
from .interference import InterferenceConfig, snr_db as compute_snr_db, transmission_success
from .mobility import rwp, smooth


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
    decision_reason: str = ""
    target_sf: int = 7
    generated_packets_total: int = 0
    dropped_packets_total: int = 0
    buffer_occupancy: int = 0
    retry_attempt: int = 0


@dataclass
class SimulationResult:
    uplink_count: int = 0
    events: list[Event] = field(default_factory=list)


@dataclass
class NodeState:
    current_sf: int
    tx_power_dbm: float
    switch_count_total: int = 0
    reward_history: list[float] = field(default_factory=list)
    last_uplink_time_s: float = 0.0
    mobility_model: str = "rwp"
    mobility_state: rwp.RandomWaypointState | smooth.SmoothState | None = None
    packet_buffer: list[GeneratedPacket] = field(default_factory=list)
    generated_packets_total: int = 0
    dropped_packets_total: int = 0
    next_radio_free_s: float = 0.0


@dataclass
class GeneratedPacket:
    packet_id: int
    retries_left: int
    attempts: int = 0


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

    def _compute_interferers(
        self,
        *,
        node_count: int,
        signal_dbm: float,
        signal_sf: int,
        interference_db: float,
        sigma: float,
    ) -> list[tuple[float, int]]:
        potential_interferers = max(node_count - 1, 0)
        if potential_interferers == 0:
            return []

        if interference_db <= 0.0 and sigma <= 0.0:
            return []

        expected = min(
            potential_interferers,
            int(max(1.0, (0.05 + (interference_db / 40.0)) * potential_interferers)),
        )
        n_interferers = self.rng.randint(0, expected)
        if n_interferers <= 0:
            return []

        sf_candidates = [7, 8, 9, 10, 11, 12]
        interferers: list[tuple[float, int]] = []
        for _ in range(n_interferers):
            relative_drop = max(0.5, interference_db + abs(self.rng.gauss(0.0, max(sigma, 0.01))))
            power_i_dbm = signal_dbm - relative_drop
            sf_i = signal_sf if self.rng.random() < 0.55 else self.rng.choice(sf_candidates)
            interferers.append((power_i_dbm, sf_i))
        return interferers

    def _init_mobility_state(self, *, mobility_model: str, speed_mps: float, area_size_m: float) -> Any:
        if mobility_model == "smooth":
            cfg = smooth.SmoothConfig(
                area_width_m=area_size_m,
                area_height_m=area_size_m,
                min_speed_mps=max(speed_mps * 0.6, 0.1),
                max_speed_mps=max(speed_mps * 1.4, 0.2),
            )
            return smooth.init_state(cfg, rng=self.rng)

        cfg = rwp.RandomWaypointConfig(
            area_width_m=area_size_m,
            area_height_m=area_size_m,
            min_speed_mps=max(speed_mps * 0.6, 0.1),
            max_speed_mps=max(speed_mps * 1.4, 0.2),
        )
        return rwp.init_state(cfg, rng=self.rng)

    def _advance_mobility(
        self,
        *,
        mobility_model: str,
        mobility_state: Any,
        dt_s: float,
        speed_mps: float,
        area_size_m: float,
    ) -> tuple[float, float]:
        dt_s = max(dt_s, 0.0)
        if mobility_model == "smooth":
            cfg = smooth.SmoothConfig(
                area_width_m=area_size_m,
                area_height_m=area_size_m,
                min_speed_mps=max(speed_mps * 0.6, 0.1),
                max_speed_mps=max(speed_mps * 1.4, 0.2),
            )
            smooth.step(mobility_state, dt_s, cfg, rng=self.rng)
        else:
            cfg = rwp.RandomWaypointConfig(
                area_width_m=area_size_m,
                area_height_m=area_size_m,
                min_speed_mps=max(speed_mps * 0.6, 0.1),
                max_speed_mps=max(speed_mps * 1.4, 0.2),
            )
            rwp.step(mobility_state, dt_s, cfg, rng=self.rng)
        return float(mobility_state.x), float(mobility_state.y)

    def _schedule_initial_events(self, nodes: list[Node]) -> list[Event]:
        queue: list[Event] = []
        for node in nodes:
            jitter = self.rng.uniform(0.0, min(node.period_s, 1.0))
            node.next_uplink_s = max(0.0, jitter)
            heapq.heappush(queue, Event(time_s=node.next_uplink_s, kind="uplink", node_id=node.node_id))
        return queue

    @staticmethod
    def _buffer_policy_for_algo(algo_name: str) -> tuple[int, int, str]:
        if algo_name in {"ucb", "ucb_forget"}:
            return 2, 4, "drop_oldest"
        if algo_name == "adr_mixra":
            return 1, 3, "drop_oldest"
        return 0, 2, "drop_newest"

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
    ) -> tuple[int, float, float, str]:
        """Calcule le SF cible et la raison via une interface commune."""

        if algo_name == "adr":
            sf, reason = recommend_sf_with_reason(current_sf=current_sf, snr_db=snr_db, cfg=adr_cfg)
            reward = (1.0 if success else -0.25) - 0.08 * airtime_s
            return sf, node_tx_power_dbm, reward, reason
        if algo_name == "adr_mixra":
            sf, tx_power_dbm, reason = adapt_link(
                current_sf=current_sf,
                current_tx_power_dbm=node_tx_power_dbm,
                snr_db=snr_db,
                pdr_estimate=1.0 if success else 0.0,
                latency_estimate_s=airtime_s,
                cfg=adr_mixra_cfg,
            )
            reward = (1.0 if success else -0.35) - 0.1 * airtime_s
            return sf, tx_power_dbm, reward, reason
        if algo_name in {"ucb", "ucb_forget"}:
            agent = mab_agents[node_id]
            arm = agent.select_arm()
            new_sf = sf_arms[arm]
            reward = (1.0 if success else -0.25) - 0.08 * airtime_s
            agent.update(arm, reward)
            reason = f"mab_reward={(1.0 if success else -0.25) - 0.08 * airtime_s:.3f}|airtime_cost={airtime_s:.3f}s|qos={'ok' if success else 'degraded'}"
            return new_sf, node_tx_power_dbm, reward, reason
        reward = (1.0 if success else -0.25) - 0.08 * airtime_s
        return current_sf, node_tx_power_dbm, reward, "no_adaptation"

    def run(
        self,
        *,
        nodes: list[Node],
        until_s: float,
        mode: str = "snir_off",
        algo: str = "adr",
        mobility_model: str = "rwp",
        speed_mps: float = 1.0,
        area_size_m: float = 1_000.0,
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
        channel_cfg = ChannelConfig(sigma_shadowing=max(sigma, 0.0))
        mobility_name = mobility_model.lower()

        mab_agents: dict[int, UCB1 | UCBForget] = {}
        node_states: dict[int, NodeState] = {}
        sf_arms = [7, 8, 9, 10, 11, 12]
        for node in nodes:
            initial_sf = int(node.meta.get("sf", self.rng.randint(8, 11)))
            node.meta.setdefault("tx_power_dbm", 14.0)
            node.meta.setdefault("switch_count", 0)
            node_states[node.node_id] = NodeState(
                current_sf=initial_sf,
                tx_power_dbm=float(node.meta.get("tx_power_dbm", 14.0)),
                switch_count_total=int(node.meta.get("switch_count", 0)),
                reward_history=list(node.meta.get("reward_history", [])),
                mobility_model=mobility_name,
                mobility_state=self._init_mobility_state(
                    mobility_model=mobility_name,
                    speed_mps=speed_mps,
                    area_size_m=area_size_m,
                ),
            )
            if algo_name == "ucb":
                mab_agents[node.node_id] = UCB1(n_arms=len(sf_arms))
            elif algo_name == "ucb_forget":
                mab_agents[node.node_id] = UCBForget(n_arms=len(sf_arms))

        max_retries, buffer_capacity, drop_policy = self._buffer_policy_for_algo(algo_name)
        packet_seq = 0

        queue = self._schedule_initial_events(nodes)
        result = SimulationResult()
        while queue:
            event = heapq.heappop(queue)
            if event.time_s > until_s:
                break

            if progress_callback is not None:
                progress_callback(min(max(event.time_s / until_s, 0.0), 1.0))

            if event.kind == "uplink":
                node = node_by_id[event.node_id]
                node_state = node_states[node.node_id]

                packet_seq += 1
                generated_packet = GeneratedPacket(packet_id=packet_seq, retries_left=max_retries)
                node_state.generated_packets_total += 1
                if len(node_state.packet_buffer) >= buffer_capacity:
                    node_state.dropped_packets_total += 1
                    if drop_policy == "drop_oldest" and node_state.packet_buffer:
                        node_state.packet_buffer.pop(0)
                        node_state.packet_buffer.append(generated_packet)
                else:
                    node_state.packet_buffer.append(generated_packet)

                result.events.append(
                    Event(
                        time_s=event.time_s,
                        kind="packet_generated",
                        node_id=node.node_id,
                        generated_packets_total=node_state.generated_packets_total,
                        dropped_packets_total=node_state.dropped_packets_total,
                        buffer_occupancy=len(node_state.packet_buffer),
                    )
                )

                if not node_state.packet_buffer:
                    next_time = event.time_s + max(node.period_s, 1e-6)
                    node.next_uplink_s = next_time
                    heapq.heappush(queue, Event(time_s=next_time, kind="uplink", node_id=node.node_id))
                    continue

                if event.time_s < node_state.next_radio_free_s:
                    next_time = event.time_s + max(node.period_s, 1e-6)
                    node.next_uplink_s = next_time
                    heapq.heappush(queue, Event(time_s=next_time, kind="uplink", node_id=node.node_id))
                    continue

                result.uplink_count += 1
                packet_in_flight = node_state.packet_buffer[0]
                packet_in_flight.attempts += 1

                dt_s = event.time_s - node_state.last_uplink_time_s
                node_x, node_y = self._advance_mobility(
                    mobility_model=node_state.mobility_model,
                    mobility_state=node_state.mobility_state,
                    dt_s=dt_s,
                    speed_mps=speed_mps,
                    area_size_m=area_size_m,
                )
                gateway_x = area_size_m / 2.0
                gateway_y = area_size_m / 2.0
                distance_m = max(math.hypot(node_x - gateway_x, node_y - gateway_y), 1.0)

                current_sf = node_state.current_sf
                airtime_s = self._airtime_s(sf=current_sf, payload_size=node.payload_size)
                signal_dbm = received_power_dbm(
                    tx_power_dbm=node_state.tx_power_dbm,
                    distance_m=distance_m,
                    cfg=channel_cfg,
                    rng=self.rng,
                )
                interferers = self._compute_interferers(
                    node_count=node_count,
                    signal_dbm=signal_dbm,
                    signal_sf=current_sf,
                    interference_db=interference_db,
                    sigma=sigma,
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

                selection = self._select_next_sf(
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
                    node_tx_power_dbm=node_state.tx_power_dbm,
                )
                if len(selection) == 4:
                    new_sf, new_tx_power_dbm, reward, decision_reason = selection
                else:
                    new_sf, decision_reason = selection
                    new_tx_power_dbm = node_state.tx_power_dbm
                    reward = (1.0 if success else -0.25) - 0.08 * airtime_s

                switched = int(new_sf != current_sf)
                if switched:
                    node_state.switch_count_total += 1
                node_state.current_sf = new_sf
                node_state.tx_power_dbm = new_tx_power_dbm
                node_state.last_uplink_time_s = event.time_s
                node_state.next_radio_free_s = event.time_s + airtime_s
                node_state.reward_history.append(reward)

                node.meta["sf"] = new_sf
                node.meta["tx_power_dbm"] = new_tx_power_dbm
                node.meta["switch_count"] = node_state.switch_count_total
                node.meta["reward_history"] = list(node_state.reward_history)

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
                        switch_count=node_state.switch_count_total,
                        decision_reason=decision_reason,
                        target_sf=new_sf,
                        generated_packets_total=node_state.generated_packets_total,
                        dropped_packets_total=node_state.dropped_packets_total,
                        buffer_occupancy=len(node_state.packet_buffer),
                        retry_attempt=packet_in_flight.attempts,
                    )
                )

                if success:
                    node_state.packet_buffer.pop(0)
                elif packet_in_flight.retries_left > 0:
                    packet_in_flight.retries_left -= 1
                else:
                    node_state.packet_buffer.pop(0)
                    node_state.dropped_packets_total += 1

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
        run_config: dict[str, Any] = {**params}

        run_config["N"] = int(params["N"])
        run_config["speed"] = float(params.get("speed", run_config.get("speed", 0.0)))

        mobility_raw = str(
            params.get(
                "mobility_model",
                params.get("model", run_config.get("mobility_model", run_config.get("model", "rwp"))),
            )
        )
        mobility_normalized = mobility_raw.strip().lower().replace("-", "_")
        run_config["mobility_model"] = "smooth" if mobility_normalized == "smooth" else "rwp"

        mode_raw = str(params.get("mode", run_config.get("mode", "snir_off")))
        mode_token = mode_raw.strip().lower().replace("-", "_")
        mode_aliases = {
            "snir_on": "snir_on",
            "sniron": "snir_on",
            "on": "snir_on",
            "snir_off": "snir_off",
            "sniroff": "snir_off",
            "off": "snir_off",
        }
        run_config["mode"] = mode_aliases.get(mode_token, "snir_off")

        algo_raw = str(params.get("algo", run_config.get("algo", "adr")))
        algo_token = algo_raw.strip().lower().replace("-", "_")
        algo_aliases = {
            "adr": "adr",
            "adr_mixra": "adr_mixra",
            "adrmixra": "adr_mixra",
            "mixra": "adr_mixra",
            "ucb": "ucb",
            "ucb_forget": "ucb_forget",
            "ucbforget": "ucb_forget",
            "ucb_f": "ucb_forget",
        }
        run_config["algo"] = algo_aliases.get(algo_token, "adr")

        run_config["gateways"] = int(params.get("gateways", run_config.get("gateways", 1)))
        run_config["sigma"] = float(params.get("sigma", run_config.get("sigma", 0.0)))
        run_config["seed"] = int(params.get("seed", run_config.get("seed", 0)))
        run_config["rep"] = int(params.get("rep", run_config.get("rep", 1)))
        return run_config

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
                    mobility_model=str(params.get("model", params.get("mobility_model", "rwp"))),
                    speed_mps=float(params.get("speed", 1.0)),
                    area_size_m=float(params.get("area_size_m", 1_000.0)),
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
