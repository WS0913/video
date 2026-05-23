import os
from pathlib import Path

# screenshots 目录
folder = Path("screenshots")

# 获取所有文件（不含文件夹）
files = [f for f in folder.iterdir() if f.is_file()]

# 按修改时间排序（从旧到新）
files.sort(key=lambda x: x.stat().st_mtime)

# =========================
# 第一步：先改成临时名字
# 防止重名冲突
# =========================

temp_files = []

for i, file in enumerate(files):
    temp_name = folder / f"__temp__{i}{file.suffix}"
    os.rename(file, temp_name)
    temp_files.append(temp_name)

# =========================
# 第二步：正式重命名
# 1.png 2.jpg 3.webp ...
# =========================

for index, temp_file in enumerate(temp_files, start=1):

    new_name = folder / f"{index}{temp_file.suffix}"

    os.rename(temp_file, new_name)

    print(f"{temp_file.name} -> {new_name.name}")

print("\n重命名完成！")