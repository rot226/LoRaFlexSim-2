from pathlib import Path

from scripts import validate_ieee_readiness as validator


def _write_csv(path: Path, content: str) -> None:
    path.write_text(content.strip() + "\n", encoding="utf-8")


def test_validate_ieee_readiness_pass(tmp_path):
    metric_csv = tmp_path / "metric_by_factor.csv"
    _write_csv(
        metric_csv,
        """
algorithm,mode,N,pdr,der,throughput_bps
adr,snir_on,50,0.93,0.02,1200
adr,snir_on,100,0.90,0.03,1100
adr,snir_on,150,0.86,0.05,980
adr,snir_off,50,0.95,0.015,1300
adr,snir_off,100,0.92,0.02,1180
adr,snir_off,150,0.90,0.03,1050
mixra,snir_on,50,0.91,0.03,1150
mixra,snir_on,100,0.87,0.04,1000
mixra,snir_on,150,0.84,0.06,920
mixra,snir_off,50,0.94,0.02,1260
mixra,snir_off,100,0.90,0.03,1120
mixra,snir_off,150,0.88,0.04,980
""",
    )

    cdf_csv = tmp_path / "sinr_cdf.csv"
    _write_csv(
        cdf_csv,
        """
algorithm,mode,sinr_db,cdf
adr,snir_on,-12,0.1
adr,snir_on,-5,0.5
adr,snir_on,2,0.95
mixra,snir_on,-11,0.12
mixra,snir_on,-4,0.55
mixra,snir_on,1,0.93
""",
    )

    exit_code = validator.main([str(tmp_path)])
    assert exit_code == 0


def test_validate_ieee_readiness_fails_on_non_monotonic_cdf(tmp_path):
    metric_csv = tmp_path / "metric_by_factor.csv"
    _write_csv(
        metric_csv,
        """
algo,mode,N,pdr
adr,snir_on,50,0.92
adr,snir_on,100,0.90
adr,snir_on,150,0.88
""",
    )

    cdf_csv = tmp_path / "sinr_cdf.csv"
    _write_csv(
        cdf_csv,
        """
algo,mode,sinr_db,cdf
adr,snir_on,-10,0.2
adr,snir_on,-6,0.6
adr,snir_on,-2,0.5
""",
    )

    exit_code = validator.main([str(tmp_path)])
    assert exit_code == 1
