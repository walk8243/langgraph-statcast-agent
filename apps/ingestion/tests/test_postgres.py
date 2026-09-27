"""PostgreSQL 初期化および速報テーブル DDL のテスト"""

from unittest.mock import MagicMock
import pytest
from src.postgres import DEFAULT_INIT_DDL, initialize_tables


def test_default_init_ddl_contains_live_game_tables():
    """DEFAULT_INIT_DDL に速報テーブルの定義が含まれることを検証"""
    assert "CREATE TABLE IF NOT EXISTS live_linescores" in DEFAULT_INIT_DDL
    assert "CREATE TABLE IF NOT EXISTS live_plays" in DEFAULT_INIT_DDL
    assert "CREATE TABLE IF NOT EXISTS live_pitches" in DEFAULT_INIT_DDL
    assert "idx_live_plays_game_inning" in DEFAULT_INIT_DDL
    assert "idx_live_pitches_game_play" in DEFAULT_INIT_DDL


def test_initialize_tables_fallback():
    """ddl_path が存在しない場合に DEFAULT_INIT_DDL が実行されることを検証"""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

    initialize_tables(mock_conn, ddl_path="/nonexistent/path/init.sql")

    mock_cursor.execute.assert_called_once_with(DEFAULT_INIT_DDL)
    mock_conn.commit.assert_called_once()
