"""batch_statcast モジュールの単体テスト"""

from unittest.mock import MagicMock, patch
import pandas as pd
import pytest

from src.batch_statcast import ingest_statcast_date_range


def test_ingest_statcast_date_range_validation():
    ch_client = MagicMock()

    # end_date < start_date
    with pytest.raises(ValueError, match="end_date .* must be greater than or equal to start_date"):
        ingest_statcast_date_range(ch_client, start_date="2024-04-05", end_date="2024-04-01")

    # step_days <= 0
    with pytest.raises(ValueError, match="step_days must be greater than 0"):
        ingest_statcast_date_range(ch_client, start_date="2024-04-01", end_date="2024-04-02", step_days=0)

    # invalid date format
    with pytest.raises(ValueError):
        ingest_statcast_date_range(ch_client, start_date="invalid-date")


@patch("src.batch_statcast.download_statcast_csv")
@patch("src.batch_statcast.insert_statcast_data")
@patch("time.sleep")
def test_ingest_statcast_date_range_success(mock_sleep, mock_insert, mock_download):
    ch_client = MagicMock()

    # 各日のモック DataFrame
    df_day1 = pd.DataFrame({"pitch_type": ["FF"], "game_date": ["2024-04-01"]})
    df_day2 = pd.DataFrame({"pitch_type": ["SL"], "game_date": ["2024-04-02"]})
    mock_download.side_effect = [df_day1, df_day2]
    mock_insert.side_effect = [100, 200]

    result = ingest_statcast_date_range(
        ch_client=ch_client,
        start_date="2024-04-01",
        end_date="2024-04-02",
        interval=2.0,
        step_days=1,
    )

    assert result["total_chunks"] == 2
    assert result["success_chunks"] == 2
    assert result["skipped_chunks"] == 0
    assert result["failed_chunks"] == 0
    assert result["total_inserted"] == 300

    # download_statcast_csv の呼び出し確認 (player_id=None)
    assert mock_download.call_count == 2
    mock_download.assert_any_call(start_date="2024-04-01", end_date="2024-04-01", player_id=None)
    mock_download.assert_any_call(start_date="2024-04-02", end_date="2024-04-02", player_id=None)

    # 最後のチャンク後は sleep しないため、1回だけ sleep が呼ばれる
    mock_sleep.assert_called_once_with(2.0)


@patch("src.batch_statcast.download_statcast_csv")
@patch("src.batch_statcast.insert_statcast_data")
@patch("time.sleep")
def test_ingest_statcast_date_range_skip_empty_and_error(mock_sleep, mock_insert, mock_download):
    ch_client = MagicMock()

    # 1日目: 正常 (10件)
    # 2日目: 空データ (0件)
    # 3日目: ダウンロード例外
    df_day1 = pd.DataFrame({"pitch_type": ["FF"]})
    df_empty = pd.DataFrame()
    mock_download.side_effect = [df_day1, df_empty, RuntimeError("Network error")]
    mock_insert.return_value = 10

    result = ingest_statcast_date_range(
        ch_client=ch_client,
        start_date="2024-04-01",
        end_date="2024-04-03",
        interval=1.0,
        step_days=1,
    )

    assert result["total_chunks"] == 3
    assert result["success_chunks"] == 1
    assert result["skipped_chunks"] == 1
    assert result["failed_chunks"] == 1
    assert result["total_inserted"] == 10

    # insert は 1 回だけ呼ばれる
    assert mock_insert.call_count == 1
    # 2回のスリープ
    assert mock_sleep.call_count == 2


@patch("src.batch_statcast.download_statcast_csv")
@patch("src.batch_statcast.insert_statcast_data")
def test_ingest_statcast_date_range_step_days(mock_insert, mock_download):
    ch_client = MagicMock()

    # 4日分を step_days=2 で 2 チャンクに分割
    mock_download.return_value = pd.DataFrame({"pitch_type": ["FF"]})
    mock_insert.return_value = 50

    result = ingest_statcast_date_range(
        ch_client=ch_client,
        start_date="2024-04-01",
        end_date="2024-04-04",
        interval=0.0,
        step_days=2,
    )

    assert result["total_chunks"] == 2
    assert result["total_inserted"] == 100
    mock_download.assert_any_call(start_date="2024-04-01", end_date="2024-04-02", player_id=None)
    mock_download.assert_any_call(start_date="2024-04-03", end_date="2024-04-04", player_id=None)
