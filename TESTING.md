Testing
=======

运行方式
-------

推荐在项目的 `.venv` 环境中执行测试：

```powershell
cd "d:\大三上\软件工程\Code\code"
.venv\Scripts\python.exe -m pytest -q
```

说明
----

- 项目包含单元测试（`tests/test_users.py`、`tests/test_products.py`）和集成测试（`tests/test_integration.py`）。
- 集成测试使用 SQLite 内存数据库（`sqlite:///:memory:`）并覆写 `get_db` 依赖以避免触碰生产数据库。

当前测试结果（我本地运行）：

- 16 passed, 18 warnings

备注
----

如需将测试自动化（CI），我可以帮你添加一个简单的 GitHub Actions workflow 来在每次提交/PR 时运行测试。