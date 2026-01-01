import frelatage
from frelatage import Input
import os

# 1. 一个极其简单的目标函数
@frelatage.instrument
def simple_target(arg1):
    # 简单的逻辑：如果两个参数拼接等于 "crash"，则报错
    if str(arg1) == "crash":
        # 抛出异常模拟崩溃
        raise RuntimeError("Boom! Crash found!")
    return True

if __name__ == "__main__":
    print("--- 开始最小化 Fuzz 测试 ---")
    
    # 2. 简单的语料库
    samples = [
        [Input(value="world")]
    ]

    # 3. 运行 Fuzzer
    # 如果这里能跑通，说明环境没问题，是之前路径的问题
    f = frelatage.Fuzzer(simple_target, samples)
    f.fuzz()
