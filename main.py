from scripts.processors.adapters.juejinfetch import JuejinFetcher

def main():
    # 实例化适配器
    juejin = JuejinFetcher()
    
    # 统一获取标准格式数据
    news_list = juejin.fetch(limit=10)
    
    # 输出检查
    for news in news_list:
        print(f"[{news.source}] {news.title} - Heat: {news.hot_score}-url:{news.url}")

if __name__ == "__main__":
    main()