from storage_abstraction import StorageManager, Tier


def test_local_smoke(tmp_path, monkeypatch):
    monkeypatch.setenv("STORAGE_ENV", "dev")
    monkeypatch.setenv("LOCAL_BASE_PATH", str(tmp_path))

    mgr = StorageManager.from_env()
    key = "a/b.txt"
    data = b"x"

    mgr.put(Tier.TEMP, key, data)

    assert mgr.exists(Tier.TEMP, key)
    assert mgr.get(Tier.TEMP, key) == data
    assert list(mgr.list(Tier.TEMP, prefix="a/")) == [key]

    mgr.delete(Tier.TEMP, key)
    assert not mgr.exists(Tier.TEMP, key)
