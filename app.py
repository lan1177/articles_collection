from flask import Flask, render_template, request, redirect, url_for, abort
from flask_caching import Cache
from feishu_api import FeishuAPI
from config import Config
import os
import datetime
import logging

# 配置日志记录
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 创建Flask应用
app = Flask(__name__)
app.config.from_object(Config)

# 配置缓存
cache = Cache(app)

# 设置缓存时间为30秒
CACHE_TIMEOUT = 30

# 初始化飞书API
feishu_api = FeishuAPI()

@app.route('/')
@cache.cached(timeout=CACHE_TIMEOUT)  # 缓存30秒
def index():
    """
    首页：展示所有文章列表
    """
    # 获取文章列表
    result = feishu_api.get_records()
    articles = result.get('records', [])
    
    # 处理首页卡片内容为点评内容（如 summary 字段），预览截取前100字
    for article in articles:
        # 只取“概要内容输出”字段，且不截断
        preview = article.get('preview', '')
        article['preview'] = preview
    
    return render_template('index.html', articles=articles)

@app.route('/article/<record_id>')
@cache.cached(timeout=CACHE_TIMEOUT)  # 缓存30秒
def article_detail(record_id):
    """
    文章详情页
    
    参数:
        record_id: 文章ID
    """
    # 获取文章详情
    article = feishu_api.get_record_by_id(record_id)
    
    if not article:
        abort(404)
        
    return render_template('detail.html', article=article)

@app.route('/search')
def search():
    q = request.args.get('q', '').strip()
    result = feishu_api.get_records()
    articles = result.get('records', [])
    matched = []
    for article in articles:
        # 搜索标题、点评和正文
        title = article.get('title', '')
        summary = article.get('summary', '') or article.get('comment', '')
        content = article.get('content', '')
        search_fields = [title, summary, content]
        if q and any(q in field for field in search_fields if field):
            # 优先在正文中提取片段
            idx = content.find(q)
            if idx != -1:
                start = max(0, idx-25)
                end = min(len(content), idx+75)
                snippet = content[start:end]
                # 高亮关键字
                snippet = snippet.replace(q, f'<mark>{q}</mark>')
                # 片段末尾加省略号
                if len(content) > end:
                    snippet = snippet.rstrip() + '……'
            else:
                # 若正文无关键字，则在点评中找
                idx2 = summary.find(q)
                if idx2 != -1:
                    start = max(0, idx2-25)
                    end = min(len(summary), idx2+75)
                    snippet = summary[start:end]
                    snippet = snippet.replace(q, f'<mark>{q}</mark>')
                    if len(summary) > end:
                        snippet = snippet.rstrip() + '……'
                else:
                    # 都没有则取正文前100字
                    snippet = content[:100]
                    if len(content) > 100:
                        snippet = snippet.rstrip() + '……'
            matched.append({
                'record_id': article.get('record_id'),
                'title': title,
                'snippet': snippet
            })
    return render_template('search.html', q=q, results=matched)

@app.errorhandler(404)
def page_not_found(e):
    """
    404错误处理
    """
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    """
    500错误处理
    """
    return render_template('500.html'), 500

@app.context_processor
def inject_globals():
    """
    注入全局变量到模板
    """
    return {
        'site_title': 'AI knowledge base',
        'now': datetime.datetime.now()
    }

# 创建必要的目录
def create_directories():
    """
    创建项目所需的目录结构
    """
    directories = [
        'static/css',
        'static/js',
        'templates'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

if __name__ == '__main__':
    # 确保目录结构存在
    create_directories()
    
    # 启动应用，使用5002端口避免端口冲突
    logger.info("正在启动应用程序，端口：5002")
    logger.info(f"缓存时间设置为{CACHE_TIMEOUT}秒")
    app.run(host='0.0.0.0', port=5002, debug=True)
