/**
 * 好文精选网站主JavaScript文件
 * 提供基本的交互功能
 */

document.addEventListener('DOMContentLoaded', function() {
    // 为文章卡片添加淡入动画
    const articleCards = document.querySelectorAll('.article-card');
    
    if (articleCards.length > 0) {
        articleCards.forEach((card, index) => {
            // 设置延迟，使卡片依次淡入
            setTimeout(() => {
                card.style.opacity = '1';
                card.style.transform = 'translateY(0)';
            }, 100 * index);
        });
    }
    
    // 平滑滚动到顶部
    const scrollToTop = () => {
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    };
    
    // 创建返回顶部按钮
    const createBackToTopButton = () => {
        const button = document.createElement('button');
        button.innerHTML = '↑';
        button.className = 'back-to-top';
        button.addEventListener('click', scrollToTop);
        
        document.body.appendChild(button);
        
        // 监听滚动事件，控制按钮显示/隐藏
        window.addEventListener('scroll', () => {
            if (window.scrollY > 300) {
                button.classList.add('visible');
            } else {
                button.classList.remove('visible');
            }
        });
    };
    
    // 添加返回顶部按钮
    createBackToTopButton();
});
