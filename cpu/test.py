import csv

# 读取 CSV 文件
input_file = 'data/2025-05-06_input.csv'  # 替换为你的 CSV 文件路径
output_file = 'data/output.txt'  # 输出文件路径

with open(input_file, 'r', encoding='utf-8') as csv_file:
    reader = csv.reader(csv_file)
    with open(output_file, 'w', encoding='utf-8') as csv_file:
        for row in reader:
            # 将每行内容以无中括号与双引号的形式保存
            csv_file.write(','.join(row) + '\n')

print(f"内容已保存到 {output_file}")