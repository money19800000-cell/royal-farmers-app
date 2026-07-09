// mobile-fix.js — 手机端动态补丁（表格 & 固定列横向滚动）
(function () {
  function fix() {
    if (window.innerWidth > 768) return;

    // 1. 含固定 px 宽度的多列 grid（如 "1fr 100px 110px …"）
    //    → 给其直接父级设置 overflow-x:auto，所有子行设 min-width
    var fixedRe = /grid-template-columns:\s*[^;]*\d+px[^;]*\d+px/;
    var processedParents = new Set();

    document.querySelectorAll('[style]').forEach(function (el) {
      if (el.dataset.mobFixed) return;
      var s = el.getAttribute('style') || '';
      if (!fixedRe.test(s)) return;

      el.dataset.mobFixed = '1';
      el.style.minWidth = '640px';

      var p = el.parentElement;
      if (!p || processedParents.has(p)) return;
      processedParents.add(p);

      // 清除可能存在的 overflow shorthand，分设 x/y
      p.style.removeProperty('overflow');
      p.style.overflowX = 'auto';
      p.style.overflowY = 'visible';
      p.style.webkitOverflowScrolling = 'touch';
    });

    // 2. <table> 元素 → 其父级允许横向滚动
    document.querySelectorAll('table').forEach(function (t) {
      if (t.dataset.mobFixed) return;
      t.dataset.mobFixed = '1';
      var p = t.parentElement;
      if (!p) return;

      p.style.removeProperty('overflow');
      p.style.overflowX = 'auto';
      p.style.overflowY = 'visible';
      p.style.webkitOverflowScrolling = 'touch';
    });
  }

  // DC 框架渲染完毕后执行（等待 [data-screen-label] 出现）
  function tryFix(attempts) {
    attempts = attempts || 0;
    if (document.querySelector('[data-screen-label]') || attempts > 20) {
      fix();
    } else {
      setTimeout(function () { tryFix(attempts + 1); }, 100);
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () { tryFix(); });
  } else {
    tryFix();
  }

  var resizeTimer;
  window.addEventListener('resize', function () {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(fix, 150);
  });
})();
