import time

import mujoco
import mujoco.viewer

xml = """
<mujoco>
  <option gravity="0 0 -9.81"/>
  <worldbody>
    <light diffuse=".5 .5 .5" pos="0 0 3" dir="0 0 -1"/>
    
    <!-- 地面：增加摩擦系数和弹性参数 -->
    <geom type="plane" size="2 2 2" rgba=".9 0 0 1"
      friction="0.1"
      euler="0.1 0 0"/>
    
    <body pos="0 0 2"> <!-- 提高初始高度，看得更清楚 -->
      <joint type="free"/>
      <!-- condim="1" 使碰撞变为纯弹性，不粘滞 -->
      <!-- solref="0.005 1" 表示更硬、更有弹性 -->
      <!-- solimp="0.7 0.9 0.001" 表示更高的弹性和更低的粘滞 -->
      <geom type="sphere" size=".1" rgba="0 .9 0 1" 
            condim="1" 
            solref="0.005 0.2" 
            solimp="0.7 0.9 0.001"/>
    </body>
  </worldbody>
</mujoco>
"""

# m = mujoco.MjModel.from_xml_path('/path/to/mjcf.xml')
m = mujoco.MjModel.from_xml_string(xml) # 从字符串中创建
d = mujoco.MjData(m) # 创建数据对象

with mujoco.viewer.launch_passive(m, d) as viewer:
    start_real = time.time() # 记录仿真开始的现实时间
    
    while viewer.is_running() and (time.time() - start_real) < 30: # 运行30秒
        step_start = time.time()

        # 执行物理步进
        mujoco.mj_step(m, d)

        # 这里的同步非常关键：每秒钟同步一次渲染状态
        viewer.sync()

        # --- 精确时间控制 ---
        # 计算当前仿真时间点对应的现实时间
        target_real_time = start_real + d.time
        
        # 1. 先用 sleep 释放大部分 CPU (如果差值大于 1ms)
        time_to_wait = target_real_time - time.time()
        if time_to_wait > 0.001:
            time.sleep(time_to_wait)
            
        # 2. 再用 busy-loop 进行微秒级精调，直到现实时间追上仿真时间
        while time.time() < target_real_time:
            pass