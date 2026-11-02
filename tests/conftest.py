"""Shared Pytest Fixtures for Phase 3 Core Skeleton & Interface Tests."""

from pathlib import Path
import pytest

from app.core.config import AppConfig
from app.core.task_manager import TaskManager
from app.schemas.script_schema import ScriptInput, SourceChannel


@pytest.fixture
def isolated_config(tmp_path: Path) -> AppConfig:
    """Provide an isolated AppConfig rooted inside pytest's temporary directory."""
    return AppConfig(base_dir=tmp_path)


@pytest.fixture
def task_manager(isolated_config: AppConfig) -> TaskManager:
    """Provide an isolated TaskManager backed by `isolated_config`."""
    return TaskManager(config=isolated_config)


@pytest.fixture
def sample_script_input() -> ScriptInput:
    """Provide a valid Dark Myth Journey to the West sample ScriptInput."""
    return ScriptInput(
        job_id="job_20261031_test01",
        source_channel=SourceChannel.WEB_UI,
        title="Ngộ Không Đại Chiến Nhị Lang Thần",
        raw_script_text=(
            "Cảnh 1: Giữa trang giấy vở nhuốm mực đen, Tôn Ngộ Không mắt đỏ rực chống Thiết Bảng Như Ý đứng đối diện Nhị Lang Thần.\n"
            "Cảnh 2: Nhị Lang Thần lao vút tới bổ mạnh Tam Tiêm Đảo xuống nhưng Ngộ Không vung gậy sắt đỡ đòn làm tóe lửa khắp mặt giấy.\n"
            "Cảnh 3: Từ đỉnh trang giấy, Bàn tay Phật Tổ khổng lồ giáng xuống trấn áp cả bầu trời hắc ám!"
        ),
        voice_id="vi-VN-NamMinhNeural",
        voice_speed=1.05,
    )
