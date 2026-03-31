import time

import mujoco
import mujoco.viewer

xml = """
<mujoco>
  <option gravity="0 0 -9.81"/>
  <worldbody>
    <light diffuse=".5 .5 .5" pos="0 0 3" dir="0 0 -1"/>
    
    <!-- 地面：增加摩擦系数和弹性参数 -->
    <geom type="plane" size="1 1 1" rgba=".9 0 0 1" friction="0.1"/>
    
    <body pos="0 0 2"> <!-- 提高初始高度，看得更清楚 -->
      <joint type="free"/>
      <!-- condim="1" 使碰撞变为纯弹性，不粘滞 -->
      <!-- solref="0.005 1" 表示更硬、更有弹性 -->
      <geom type="sphere" size=".1" rgba="0 .9 0 1" 
            condim="1" 
            solref="0.005 0.3" 
            solimp="0.9 0.95 0.001"/>
    </body>
  </worldbody>
</mujoco>
"""

# m = mujoco.MjModel.from_xml_path('/path/to/mjcf.xml')
m = mujoco.MjModel.from_xml_string(xml)
d = mujoco.MjData(m)

with mujoco.viewer.launch_passive(m, d) as viewer:
    start_real = time.time()
    
    while viewer.is_running() and (time.time() - start_real) < 30:
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