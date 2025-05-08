import pandas as pd
import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler
from datetime import date
import os
import logging
from typing import Dict, Tuple, Optional

CONFIG = {
    "DATA_DIR": "./ana",
    "MIN_SAMPLES_FACTOR": 0.1,
    "QUANTILE_THRESHOLD": 0.95,
    "MAX_EPS_RATIO": 1.5,
    "MIN_DATA_SIZE": 20
}

os.makedirs(CONFIG["DATA_DIR"], exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def dynamic_min_samples(n_samples: int) -> int:
    """动态计算最小样本量"""
    return max(5, int(CONFIG["MIN_SAMPLES_FACTOR"] * np.log(n_samples + 1)))

def calculate_eps(data: np.ndarray) -> Optional[float]:
    """动态计算eps值（结合拐点检测和分位数）"""
    try:
        n_samples = data.shape[0]
        min_samples = dynamic_min_samples(n_samples)
        
        # 计算k-distance
        neighbors = NearestNeighbors(n_neighbors=min_samples)
        neighbors.fit(data)
        distances, _ = neighbors.kneighbors(data)
        k_distances = np.sort(distances[:, -1])
        
        # 拐点检测逻辑
        eps_auto = k_distances[-1]  # 默认使用最大值
        if n_samples >= CONFIG["MIN_DATA_SIZE"]:
            try:
                # 计算二阶差分
                gradients = np.gradient(k_distances)
                second_derivatives = np.gradient(gradients)
                
                # 寻找正二阶导数的拐点
                candidate_indices = np.where(second_derivatives > 0)[0]
                if len(candidate_indices) > 0:
                    eps_auto = k_distances[candidate_indices[-1]]
            except Exception as e:
                logger.debug(f"拐点检测失败: {str(e)}，使用备用方法")
        
        # 计算分位数阈值
        eps_quantile = np.quantile(k_distances, CONFIG["QUANTILE_THRESHOLD"])
        
        # 确定最终eps（取最小值并限制最大倍数）
        eps = min(eps_auto, eps_quantile, CONFIG["MAX_EPS_RATIO"] * eps_auto)
        
        # 安全校验
        if eps <= 0 or eps > np.max(k_distances) * 1.2:
            return np.quantile(k_distances, 0.9)
        return eps
    except Exception as e:
        logger.error(f"EPS计算失败: {str(e)}")
        return None

def process_column(data: pd.Series) -> Tuple[pd.Series, Dict]:
    """处理单个数据列"""
    col_name = data.name
    original_data = data.copy()
    stats = {
        "error": None,
        "eps": None,
        "noise_ratio": 0.0,
        "n_clusters": 0,
        "cleaned_mean": None,
        "scaled_var": None
    }

    # 预处理数据
    valid_data = data.dropna()
    if len(valid_data) < 5:
        stats["error"] = "insufficient_data"
        return original_data, stats

    try:
        # 数据标准化
        scaler = StandardScaler()
        scaled = scaler.fit_transform(valid_data.values.reshape(-1, 1))
        
        # 动态计算参数
        eps = calculate_eps(scaled)
        if eps is None or eps <= 0:
            stats["error"] = "invalid_eps"
            return original_data, stats
        
        min_samples = dynamic_min_samples(len(valid_data))
        
        # 执行DBSCAN聚类
        labels = DBSCAN(eps=eps, min_samples=min_samples).fit_predict(scaled)
        
        # 标记噪声点
        noise_mask = labels == -1
        cleaned_idx = valid_data.index[~noise_mask]
        
        # 计算标准化方差
        if len(cleaned_idx) > 1:
            cleaned_scaled = scaled[~noise_mask]
            stats["scaled_var"] = round(float(np.var(cleaned_scaled)), 4)
        
        # 生成清洗后数据
        cleaned_data = valid_data.copy()
        cleaned_data.iloc[noise_mask] = np.nan
        
        # 更新统计信息
        cleaned_mean = cleaned_data.mean() if not cleaned_data.dropna().empty else None
        
        stats.update({
            "eps": round(eps, 4),
            "noise_ratio": round(noise_mask.mean(), 4),
            "n_clusters": len(np.unique(labels)) - (1 if -1 in labels else 0),
            "cleaned_mean": round(cleaned_mean, 4) if cleaned_mean else None
        })

        # 应用清洗结果
        result = original_data.copy()
        result.loc[cleaned_data.index] = cleaned_data
        return result, stats
        
    except Exception as e:
        logger.error(f"列 {col_name} 处理异常: {str(e)}")
        stats["error"] = "processing_error"
        return original_data, stats

def main():
    today = date.today().strftime("%Y-%m-%d")
    input_path = os.path.join(CONFIG["DATA_DIR"], f"{today}_iqr.csv")
    
    try:
        df = pd.read_csv(input_path)
        cleaned_df = pd.DataFrame(index=df.index)
        stats_data = []
        
        for col in df.columns:
            logger.info(f"正在处理列: {col}")
            cleaned_series, stats = process_column(df[col])
            cleaned_df[col] = cleaned_series
            stats["column"] = col
            stats_data.append(stats)
        
        # 保存结果
        cleaned_df.to_csv(
            os.path.join(CONFIG["DATA_DIR"], f"{today}_dbscan.csv"), 
            index=False
        )
        pd.DataFrame(stats_data).set_index("column").to_csv(
            os.path.join(CONFIG["DATA_DIR"], f"{today}_dbscan_stats.csv")
        )
        logger.info(f"处理完成，有效处理 {len(stats_data)} 列数据")
        
    except Exception as e:
        logger.error(f"主流程失败: {str(e)}")

if __name__ == "__main__":
    main()