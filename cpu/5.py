import pandas as pd
from datetime import date

# 输入日期（注意保持文件名与日期格式一致）
date_str = date.today().strftime("%Y-%m-%d")  # 重命名变量避免与date模块冲突

# 读取文件
dbscan_path = f"ana/{date_str}_dbscan.csv"
stats_path = f"ana/{date_str}_dbscan_stats.csv"

# 读取第一个文件并提取型号
df_dbscan = pd.read_csv(dbscan_path)
models = df_dbscan.columns.tolist()

# 读取第二个文件并建立型号索引
df_stats = pd.read_csv(stats_path).set_index("column")

# 第一阶段：处理众数和均值逻辑（强制转换为整数）
results = []
for model in models:
    data = df_dbscan[model]
    counts = data.value_counts()
    filtered_counts = counts[counts >= 5]
    
    if not filtered_counts.empty:
        max_count = filtered_counts.max()
        candidates = filtered_counts[filtered_counts == max_count].index
        mode = min(candidates)
        results.append(int(mode))  # 确保众数为整数
    else:
        if model in df_stats.index:
            record = df_stats.loc[model]
            if record["scaled_var"] < 0.8:
                # 均值四舍五入后转整数
                cleaned_mean = record["cleaned_mean"]
                results.append(int(round(cleaned_mean)))  # 关键修改点
            else:
                results.append(None)
        else:
            results.append(None)

# 第二阶段：填充剩余空值为最小值（强制为整数）
for i in range(len(results)):
    if results[i] is None:
        model = models[i]
        numeric_series = pd.to_numeric(df_dbscan[model], errors='coerce')
        valid_values = numeric_series.dropna()
        
        if not valid_values.empty:
            # 取最小值后四舍五入并转整数
            min_val = valid_values.min()
            results[i] = int(round(min_val))  # 关键修改点
        else:
            print(f"警告: 型号 {model} 无有效数值数据")

# 创建结果DataFrame（列名动态化）
result_df = pd.DataFrame({
    "name": models,          # 第一列固定为name
    date_str: results        # 第二列名为当天日期
})

# 保存结果
output_path = f"result/{date_str}_od.csv"
result_df.to_csv(output_path, index=False)

print(f"处理完成，结果已保存至：{output_path}")