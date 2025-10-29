## 快速测试说明

在虚拟环境中安装依赖并运行 pytest 来执行快速集成测试：

fish shell 示例：

```fish
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest -q
```

测试文件：`management/tests/test_api_quick.py` — 它会在临时 sqlite 文件上运行一次注册/登录/建教师/预约/冲突检查的流程。

