/* ==========================================================================
   AI 实践库 · 固定脚本
   数据来源：data/catalog.js、data/lesson-<id>.js（由 tools/ingest.py 生成）
   新增课程时不需要修改本文件。
   ========================================================================== */

(function () {
  'use strict';

  var K_PROGRESS = 'learning-site:progress:';
  var K_LAST = 'learning-site:last';
  var K_SPLIT = 'learning-site:split';
  var reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ---------------- utils ---------------- */

  function $(sel, root) { return (root || document).querySelector(sel); }
  function $$(sel, root) { return Array.prototype.slice.call((root || document).querySelectorAll(sel)); }
  function el(tag, cls, text) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text != null) n.textContent = text;
    return n;
  }
  function pad(n) { return String(n).padStart(2, '0'); }
  function format(t) {
    t = Math.max(0, Math.floor(Number(t) || 0));
    var h = Math.floor(t / 3600);
    return (h ? h + ':' : '') + pad(Math.floor(t / 60) % 60) + ':' + pad(t % 60);
  }
  function monthLabel(key) {
    var m = /^(\d{4})-(\d{2})$/.exec(key || '');
    return m ? m[1] + ' 年 ' + Number(m[2]) + ' 月' : (key || '未归类');
  }
  function monthBadge(key) {
    var m = /^(\d{4})-(\d{2})$/.exec(key || '');
    return m ? m[1].slice(2) + '.' + m[2] : '--';
  }
  function read(key, fallback) {
    try { var v = JSON.parse(localStorage.getItem(key)); return v == null ? fallback : v; }
    catch (e) { return fallback; }
  }
  function write(key, value) {
    try { localStorage.setItem(key, JSON.stringify(value)); } catch (e) {}
  }
  function loadScript(src, globalName) {
    return new Promise(function (resolve, reject) {
      var s = document.createElement('script');
      s.src = src;
      s.onload = function () {
        var data = window[globalName];
        delete window[globalName];
        data ? resolve(data) : reject(new Error('数据格式异常：' + src));
      };
      s.onerror = function () { reject(new Error('无法加载 ' + src)); };
      document.head.appendChild(s);
    });
  }

  function statePage(mount, title, message, actionText, actionHref) {
    mount.innerHTML = '';
    var page = el('main', 'state-page');
    page.appendChild(el('span', 'eyebrow', 'AI 实践库'));
    page.appendChild(el('h1', null, title));
    if (message) page.appendChild(el('p', null, message));
    if (actionText) {
      var a = el('a', 'primary-link', actionText);
      a.href = actionHref || './index.html';
      page.appendChild(a);
    }
    mount.appendChild(page);
  }

  function renderTopbar(activePage, query) {
    var bar = el('header', 'topbar');
    var brand = el('a', 'brand');
    brand.href = './index.html';
    brand.appendChild(el('span', 'brand-mark', 'AI'));
    brand.appendChild(el('span', 'brand-name', (window.__SITE__ && window.__SITE__.brand) || 'AI 实践库'));
    bar.appendChild(brand);

    var nav = el('nav', 'global-nav');
    var bArchive = el('button', activePage === 'archive' ? 'active' : null, '分享档案');
    bArchive.addEventListener('click', function () { location.href = './index.html'; });
    nav.appendChild(bArchive);
    if (activePage === 'lesson') {
      var bNow = el('button', 'active', '当前阅读');
      nav.appendChild(bNow);
    }
    bar.appendChild(nav);

    var tools = el('div', 'header-tools');
    if (activePage === 'archive') {
      var form = el('form', 'header-search');
      var input = el('input');
      input.type = 'search';
      input.placeholder = '搜索分享';
      input.value = query || '';
      input.setAttribute('aria-label', '顶部搜索分享');
      form.appendChild(input);
      var btn = el('button', null, '\u2315');
      btn.type = 'submit';
      btn.setAttribute('aria-label', '搜索');
      form.appendChild(btn);
      form.addEventListener('submit', function (e) {
        e.preventDefault();
        location.hash = '';
        var val = input.value.trim();
        location.search = val ? '?q=' + encodeURIComponent(val) : '';
      });
      tools.appendChild(form);
    }
    tools.appendChild(el('span', 'header-note', '技术运营部'));
    bar.appendChild(tools);
    document.body.insertBefore(bar, document.body.firstChild);
  }

  /* ==================== archive page ==================== */

  function initArchive() {
    var mount = $('#app');
    var params = new URLSearchParams(location.search);
    var query = params.get('q') || '';
    var month = params.get('m') || '';
    var sortOrder = read('learning-site:sort', 'newest');
    var catalog = [];

    loadScript('data/catalog.js', '__CATALOG__').then(function (data) {
      catalog = (data && data.lessons) || [];
      window.__SITE__ = (data && data.site) || {};
      document.title = (window.__SITE__.brand || 'AI 实践库') + ' · 分享档案';
      renderTopbar('archive', query);
      render();
    }).catch(function (err) {
      statePage(mount, '还没有可用的分享',
        '用 tools/ingest.py 导入第一场分享，然后刷新本页。', '重新加载', location.pathname);
      console.error(err);
    });

    function filtered() {
      var q = query.trim().toLowerCase();
      var list = catalog.filter(function (x) {
        if (month && x.month !== month) return false;
        if (!q) return true;
        return [x.title, x.speaker, x.source, (x.tags || []).join(' ')]
          .join(' ').toLowerCase().indexOf(q) >= 0;
      });
      list.sort(function (a, b) {
        var d = String(b.date || '').localeCompare(String(a.date || ''));
        if (d !== 0) return sortOrder === 'newest' ? d : -d;
        return (a.order || 0) - (b.order || 0);
      });
      return list;
    }

    function render() {
      mount.innerHTML = '';
      var page = el('div', 'archive');
      page.appendChild(renderIntro());
      page.appendChild(renderMonthNav());
      page.appendChild(renderBody());
      mount.appendChild(page);
    }

    function renderIntro() {
      var intro = el('section', 'archive-intro');
      var left = el('div');
      left.appendChild(el('span', 'eyebrow', 'TECH OPS · LEARNING ARCHIVE'));
      left.appendChild(el('h1', null, '分享档案'));
      left.appendChild(el('p', null, '视频与图文笔记 · 点开任意一场，边看边读'));
      intro.appendChild(left);

      var totalSeconds = catalog.reduce(function (s, x) { return s + (Number(x.duration) || 0); }, 0);
      var months = {};
      catalog.forEach(function (x) { months[x.month] = 1; });
      var stats = el('div', 'archive-stats');
      [[catalog.length, '场分享'], [Object.keys(months).length, '个月份'],
       [Math.max(1, Math.round(totalSeconds / 3600)), '小时内容']].forEach(function (pair) {
        var d = el('div');
        var s = el('strong', null, String(pair[0]));
        d.appendChild(s);
        d.appendChild(el('span', null, pair[1]));
        stats.appendChild(d);
      });
      intro.appendChild(stats);
      return intro;
    }

    function renderMonthNav() {
      var nav = el('nav', 'month-nav');
      nav.setAttribute('aria-label', '月份导航');
      nav.appendChild(el('span', 'eyebrow', '分享目录'));

      var counts = {};
      catalog.forEach(function (x) { counts[x.month] = (counts[x.month] || 0) + 1; });

      var all = el('button', month ? null : 'active');
      all.appendChild(el('span', null, '全部分享'));
      all.appendChild(el('span', null, String(catalog.length)));
      all.addEventListener('click', function () { setMonth(''); });
      nav.appendChild(all);

      Object.keys(counts).sort().reverse().forEach(function (key) {
        var b = el('button', month === key ? 'active' : null);
        b.appendChild(el('span', null, monthLabel(key)));
        b.appendChild(el('span', null, String(counts[key])));
        b.addEventListener('click', function () { setMonth(key); });
        nav.appendChild(b);
      });
      return nav;
    }

    function setMonth(value) {
      month = value;
      var p = new URLSearchParams();
      if (query) p.set('q', query);
      if (month) p.set('m', month);
      history.replaceState(null, '', p.toString() ? '?' + p.toString() : location.pathname);
      render();
    }

    function renderBody() {
      var body = el('section', 'archive-body');
      var list = filtered();

      var tools = el('div', 'archive-tools');
      var head = el('div');
      head.appendChild(el('h2', null, month ? monthLabel(month) : '全部分享'));
      head.appendChild(el('span', null, list.length + ' 场分享'));
      tools.appendChild(head);

      var search = el('label', 'tool-search');
      search.appendChild(el('span', null, '\u2315'));
      var input = el('input');
      input.type = 'search';
      input.placeholder = '搜索主题、讲者、关键词';
      input.value = query;
      input.setAttribute('aria-label', '搜索分享');
      search.appendChild(input);
      if (query) {
        var clear = el('button', null, '\u00d7');
        clear.type = 'button';
        clear.setAttribute('aria-label', '清除搜索');
        clear.addEventListener('click', function () { setQuery(''); });
        search.appendChild(clear);
      }
      search.addEventListener('submit', function (e) { e.preventDefault(); });
      input.addEventListener('input', debounce(function () { setQuery(input.value); }, 260));
      tools.appendChild(search);

      var sel = el('select');
      sel.setAttribute('aria-label', '排列顺序');
      [['newest', '最近分享优先'], ['oldest', '最早分享优先']].forEach(function (o) {
        var opt = el('option', null, o[1]);
        opt.value = o[0];
        if (o[0] === sortOrder) opt.selected = true;
        sel.appendChild(opt);
      });
      sel.addEventListener('change', function () {
        sortOrder = sel.value;
        write('learning-site:sort', sortOrder);
        render();
      });
      tools.appendChild(sel);
      body.appendChild(tools);

      if (!list.length) {
        var empty = el('div', 'archive-empty');
        empty.appendChild(el('h3', null, catalog.length ? '没有找到相关分享' : '第一场分享，从这里开始'));
        empty.appendChild(el('p', null, catalog.length ? '换个关键词，或浏览全部月份。' : '资料导入完成后，这里会展示视频与图文笔记。'));
        var btn = el('button', null, catalog.length ? '查看全部分享' : '重新加载');
        btn.addEventListener('click', function () {
          if (catalog.length) { setMonth(''); setQuery(''); }
          else location.reload();
        });
        empty.appendChild(btn);
        body.appendChild(empty);
      } else {
        groupByMonth(list).forEach(function (group) {
          var sec = el('section', 'month-group');
          var header = el('header');
          var left = el('div');
          left.appendChild(el('span', 'month-badge', monthBadge(group.month)));
          left.appendChild(el('h3', null, monthLabel(group.month)));
          left.appendChild(el('span', null, group.items.length + ' 场分享'));
          header.appendChild(left);
          header.appendChild(el('time', null, group.items[0].date || ''));
          sec.appendChild(header);

          group.items.forEach(function (item) {
            sec.appendChild(renderRow(item));
          });
          body.appendChild(sec);
        });
      }

      var footer = el('footer', 'archive-footer');
      footer.appendChild(el('span', null, '技术运营 · AI 实践库'));
      footer.appendChild(el('span', null, '把经验留下，让实践继续。'));
      body.appendChild(footer);
      return body;
    }

    function renderRow(item) {
      var row = el('button', 'archive-row');
      row.addEventListener('click', function () {
        write(K_LAST, item.id);
        location.href = './lesson.html?id=' + encodeURIComponent(item.id);
      });
      row.appendChild(el('span', 'row-order', pad(item.order || 0)));

      var main = el('div', 'row-main');
      main.appendChild(el('h4', null, item.title));
      var meta = el('p');
      meta.appendChild(document.createTextNode(item.speaker || '分享人未记录'));
      meta.appendChild(el('span', null, (item.sceneCount || 0) + ' 章节 · 图文笔记'));
      main.appendChild(meta);
      row.appendChild(main);

      row.appendChild(el('time', null, format(item.duration)));
      var open = el('span', 'row-open', '展开阅读');
      open.appendChild(el('span', null, '\u2197'));
      row.appendChild(open);
      return row;
    }

    function setQuery(value) {
      query = value;
      var scrollY = window.scrollY;
      var p = new URLSearchParams();
      if (query) p.set('q', query);
      if (month) p.set('m', month);
      history.replaceState(null, '', p.toString() ? '?' + p.toString() : location.pathname);
      render();
      window.scrollTo(0, scrollY);
      var input = $('.tool-search input');
      if (input) { input.focus(); input.setSelectionRange(input.value.length, input.value.length); }
    }
  }

  function groupByMonth(list) {
    var out = [];
    list.forEach(function (item) {
      var g = out[out.length - 1];
      if (!g || g.month !== item.month) { g = { month: item.month, items: [] }; out.push(g); }
      g.items.push(item);
    });
    return out;
  }

  var debounceTimer;
  function debounce(fn, wait) {
    return function () {
      var args = arguments, self = this;
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(function () { fn.apply(self, args); }, wait);
    };
  }

  /* ==================== lesson page ==================== */

  function initLesson() {
    var mount = $('#app');
    var params = new URLSearchParams(location.search);
    var id = params.get('id') || read(K_LAST, null);

    var catalogData = null;
    var lesson = null;
    var video = null;
    var reading = null;
    var current = 0;
    var following = true;
    var mode = 'notes';
    var activeIndex = -1;
    var lastFollowKey = '';
    var lastSavedSlot = -1;
    var pendingTime = 0;

    loadScript('data/catalog.js', '__CATALOG__').then(function (data) {
      catalogData = data || { site: {}, lessons: [] };
      window.__SITE__ = catalogData.site || {};
      renderTopbar('lesson', '');
      var found = (catalogData.lessons || []).find(function (x) { return x.id === id; });
      if (!found) {
        found = (catalogData.lessons || []).slice().sort(function (a, b) {
          return String(b.date || '').localeCompare(String(a.date || ''));
        })[0];
      }
      if (!found) {
        statePage(mount, '还没有可用的分享', '先导入一门课，这里就能边看边读。', '返回目录', './index.html');
        return null;
      }
      id = found.id;
      return loadScript('data/lesson-' + encodeURIComponent(id) + '.js', '__LESSON__');
    }).then(function (data) {
      if (!data) return;
      lesson = data;
      write(K_LAST, lesson.id);
      renderLesson();
    }).catch(function (err) {
      statePage(mount, '内容暂时无法加载', String(err && err.message || err), '返回目录', './index.html');
    });

    function renderLesson() {
      mount.innerHTML = '';
      mount.appendChild(renderHeading());

      var workspace = el('div', 'workspace');
      workspace.id = 'workspace';
      var savedSplit = Number(read(K_SPLIT, 51));
      setSplitStyle(workspace, isFinite(savedSplit) ? clamp(savedSplit, 25, 75) : 51);

      workspace.appendChild(renderWatchPane());
      workspace.appendChild(renderDivider(workspace));
      workspace.appendChild(renderReadPane());
      mount.appendChild(workspace);

      video = $('#video');
      reading = $('#reading');
      bindVideo();

      pendingTime = clamp(Number(read(K_PROGRESS + lesson.id, 0)) || 0, 0, Math.max(0, (lesson.duration || 1) - 1));
      updateActive(true);
    }

    function renderHeading() {
      var head = el('div', 'lesson-heading');

      var crumb = el('div', 'breadcrumb');
      var back = el('button', null, '全部分享');
      back.addEventListener('click', function () { location.href = './index.html'; });
      crumb.appendChild(back);
      crumb.appendChild(el('span', null, '/'));
      crumb.appendChild(el('span', null, monthLabel(lesson.month)));
      crumb.appendChild(el('span', 'heading-date', lesson.date || ''));
      head.appendChild(crumb);

      var titleLine = el('div', 'title-line');
      titleLine.appendChild(el('h1', null, lesson.title));
      var browse = el('button', 'browse-button');
      browse.appendChild(el('span', null, '\u2637'));
      browse.appendChild(document.createTextNode(' 切换分享'));
      browse.addEventListener('click', function () { location.href = './index.html'; });
      titleLine.appendChild(browse);
      head.appendChild(titleLine);

      var byline = el('div', 'byline');
      byline.appendChild(el('span', null, lesson.speaker || '分享人未记录'));
      byline.appendChild(el('span', 'dot', '\u00b7'));
      byline.appendChild(el('span', null, format(lesson.duration) + ' 视频'));
      byline.appendChild(el('span', 'dot', '\u00b7'));
      byline.appendChild(el('span', null, (lesson.scenes || []).length + ' 个章节'));
      if (lesson.sourceUrl) {
        var link = el('a', null, (lesson.source || '原始视频') + ' \u2197');
        link.href = lesson.sourceUrl;
        link.target = '_blank';
        link.rel = 'noopener';
        byline.appendChild(link);
      }
      head.appendChild(byline);
      return head;
    }

    function renderWatchPane() {
      var pane = el('section', 'watch-pane');
      pane.id = 'watch-pane';
      pane.setAttribute('aria-label', '视频与章节');

      var shell = el('div', 'video-shell');
      var v = document.createElement('video');
      v.id = 'video';
      v.controls = true;
      v.playsInline = true;
      v.preload = 'metadata';
      v.setAttribute('aria-label', lesson.title);
      if (lesson.poster) v.poster = lesson.poster;
      v.src = lesson.video;
      shell.appendChild(v);
      pane.appendChild(shell);

      var caption = el('div', 'playback-caption');
      var dot = el('span', 'status-indicator');
      dot.id = 'status-dot';
      caption.appendChild(dot);
      var statusText = el('span', null, '随时回到现场');
      statusText.id = 'status-text';
      caption.appendChild(statusText);
      var time = el('span', 'playback-time');
      var now = el('span', null, '00:00');
      now.id = 'time-now';
      time.appendChild(now);
      time.appendChild(el('span', null, '/ ' + format(lesson.duration)));
      caption.appendChild(time);
      pane.appendChild(caption);

      var chapterHeading = el('div', 'chapter-heading');
      chapterHeading.appendChild(el('h2', null, '内容章节'));
      var counter = el('span');
      counter.id = 'chapter-counter';
      chapterHeading.appendChild(counter);
      pane.appendChild(chapterHeading);

      var list = el('div', 'chapter-list');
      list.setAttribute('aria-label', '选择章节');
      (lesson.scenes || []).forEach(function (scene, i) {
        var b = el('button');
        b.dataset.index = String(i);
        b.appendChild(el('span', 'chapter-index', pad(i + 1)));
        b.appendChild(el('span', 'chapter-name', scene.title));
        b.appendChild(el('time', null, format(scene.start)));
        b.appendChild(el('span', 'chapter-arrow', '\u2197'));
        b.addEventListener('click', function () { seek(scene.start, true); });
        list.appendChild(b);
      });
      pane.appendChild(list);

      var note = el('div', 'watch-note');
      note.appendChild(el('span', null, '\u2197'));
      note.appendChild(el('p', null, '遇到值得回看的地方，点右侧时间或画面，回到分享现场。'));
      pane.appendChild(note);
      return pane;
    }

    function renderDivider(workspace) {
      var d = el('div', 'pane-divider');
      d.setAttribute('role', 'separator');
      d.tabIndex = 0;
      d.setAttribute('aria-label', '调整播放器和图文宽度');
      d.setAttribute('aria-orientation', 'vertical');
      d.title = '拖动调整宽度 · 双击恢复默认 · 方向键微调';
      d.appendChild(el('span'));

      var drag = null;
      d.addEventListener('pointerdown', function (e) {
        if (e.button !== 0) return;
        e.preventDefault();
        var watch = $('.watch-pane').getBoundingClientRect().width;
        var read = $('.read-pane').getBoundingClientRect().width;
        drag = { id: e.pointerId, x: e.clientX, ratio: watch / (watch + read) * 100, width: watch + read };
        d.setPointerCapture(e.pointerId);
        workspace.classList.add('resizing');
      });
      d.addEventListener('pointermove', function (e) {
        if (!drag || drag.id !== e.pointerId) return;
        var next = clamp(drag.ratio + (e.clientX - drag.x) / drag.width * 100, 25, 75);
        setSplitStyle(workspace, next);
      });
      function end(e) {
        if (!drag || drag.id !== e.pointerId) return;
        drag = null;
        workspace.classList.remove('resizing');
        write(K_SPLIT, Number(workspace.style.getPropertyValue('--watch-size').replace('fr', '')) || 51);
        if (d.hasPointerCapture(e.pointerId)) d.releasePointerCapture(e.pointerId);
      }
      d.addEventListener('pointerup', end);
      d.addEventListener('pointercancel', end);
      d.addEventListener('dblclick', function () { setSplitStyle(workspace, 51); write(K_SPLIT, 51); });
      d.addEventListener('keydown', function (e) {
        var step = e.shiftKey ? 10 : 2;
        var cur = Number(workspace.style.getPropertyValue('--watch-size').replace('fr', '')) || 51;
        if (e.key === 'Enter') { setSplitStyle(workspace, 51); write(K_SPLIT, 51); }
        else if (e.key === 'ArrowLeft' || e.key === 'ArrowRight') {
          var next = clamp(cur + (e.key === 'ArrowLeft' ? -step : step), 25, 75);
          setSplitStyle(workspace, next);
          write(K_SPLIT, next);
        } else return;
        e.preventDefault();
      });
      return d;
    }

    function setSplitStyle(workspace, ratio) {
      workspace.style.setProperty('--watch-size', ratio + 'fr');
      workspace.style.setProperty('--read-size', (100 - ratio) + 'fr');
    }

    function renderReadPane() {
      var pane = el('section', 'read-pane');
      pane.id = 'read-pane';
      pane.setAttribute('aria-label', '图文笔记');

      var toolbar = el('div', 'reading-toolbar');
      var tabs = el('div', 'mode-tabs');
      tabs.setAttribute('role', 'group');
      var bNotes = el('button', 'selected', '图文笔记');
      var bCues = el('button');
      bCues.appendChild(document.createTextNode('原话 '));
      bCues.appendChild(el('span', null, String((lesson.cues || []).length)));
      if (!(lesson.cues || []).length) bCues.disabled = true;
      bNotes.addEventListener('click', function () { setMode('notes'); });
      bCues.addEventListener('click', function () { setMode('cues'); });
      tabs.appendChild(bNotes);
      tabs.appendChild(bCues);
      toolbar.appendChild(tabs);

      var follow = el('label', 'follow-control');
      var cb = el('input');
      cb.type = 'checkbox';
      cb.checked = true;
      cb.id = 'follow-toggle';
      follow.appendChild(cb);
      follow.appendChild(el('span', 'switch'));
      var followText = el('span', null, '跟随播放');
      followText.id = 'follow-text';
      follow.appendChild(followText);
      cb.addEventListener('change', function () {
        following = cb.checked;
        if (following) { scrollToActive(true); }
        syncFollowUI();
      });
      toolbar.appendChild(follow);
      pane.appendChild(toolbar);

      var paused = el('div', 'follow-paused');
      paused.id = 'follow-paused';
      paused.hidden = true;
      paused.appendChild(el('span', null, '自由阅读中'));
      var resume = el('button', null, '回到当前播放位置 \u2193');
      resume.addEventListener('click', function () {
        following = true;
        cb.checked = true;
        syncFollowUI();
        scrollToActive(true);
      });
      paused.appendChild(resume);
      pane.appendChild(paused);

      var scroll = el('div', 'reading-scroll');
      scroll.id = 'reading';
      scroll.tabIndex = 0;
      scroll.setAttribute('aria-label', '可滚动的阅读内容');
      scroll.addEventListener('wheel', function () { if (following) setFollowing(false); }, { passive: true });
      scroll.addEventListener('touchmove', function () { if (following) setFollowing(false); }, { passive: true });
      pane.appendChild(scroll);

      scroll.appendChild(renderArticleBody());

      var footer = el('footer', 'reading-footer');
      var hint = el('span', null, '图文按章节定位');
      hint.id = 'reading-hint';
      footer.appendChild(hint);
      var pct = el('span', null, '0% 已播放');
      pct.id = 'reading-pct';
      footer.appendChild(pct);
      pane.appendChild(footer);
      return pane;
    }

    function renderArticleBody() {
      var body = el('div', 'article-body');

      var intro = el('div', 'reading-intro');
      intro.appendChild(el('span', 'eyebrow', 'WATCH · READ · PRACTICE'));
      intro.appendChild(el('p', null, '让每一次实践，都可以被重新学习。'));
      body.appendChild(intro);

      if (lesson.summary) {
        var sum = el('div', 'lesson-summary');
        sum.appendChild(el('strong', null, '内容摘要'));
        sum.appendChild(el('p', null, lesson.summary));
        body.appendChild(sum);
      }

      (lesson.scenes || []).forEach(function (scene, i) {
        var sec = el('article', 'scene');
        sec.id = 'scene-' + i;

        var kicker = el('div', 'scene-kicker');
        kicker.appendChild(el('span', null, 'CHAPTER ' + pad(i + 1)));
        var play = el('button', null, '\u25b7 ' + format(scene.start));
        play.setAttribute('aria-label', '播放章节 ' + scene.title);
        play.addEventListener('click', function () { seek(scene.start, true); });
        kicker.appendChild(play);
        sec.appendChild(kicker);

        if (scene.title) sec.appendChild(el('h2', null, scene.title));

        if (scene.image) {
          var frame = el('button', 'frame-button');
          frame.setAttribute('aria-label', '播放截图位置 ' + format(scene.frameTime));
          var img = el('img');
          img.src = scene.image;
          img.alt = scene.visual || scene.title || '';
          img.loading = 'lazy';
          frame.appendChild(img);
          frame.appendChild(el('span', 'frame-badge', '\u2197 回看画面 ' + format(scene.frameTime)));
          frame.addEventListener('click', function () { seek(scene.frameTime != null ? scene.frameTime : scene.start, true); });
          sec.appendChild(frame);
        }
        if (scene.visual) sec.appendChild(el('p', 'image-caption', scene.visual));

        (scene.paragraphs || []).forEach(function (para) {
          var p = el('p', 'paragraph' + (para.speaker ? '' : (scene.paragraphs.indexOf(para) ? ' is-cont' : '')));
          p.title = '点击回听本章节';
          if (para.speaker) {
            var who = el('span', 'who', para.speaker);
            p.appendChild(who);
            if (para.role) p.appendChild(el('span', 'role', '（' + para.role + '）'));
            p.appendChild(document.createTextNode('：'));
          }
          p.appendChild(document.createTextNode(para.text));
          p.addEventListener('click', function () {
            if (window.getSelection && window.getSelection().toString().trim()) return;
            seek(scene.start, true);
          });
          sec.appendChild(p);
        });

        var listen = el('button', 'listen-link');
        listen.appendChild(document.createTextNode('\u21b6 回听本章节 '));
        listen.appendChild(el('time', null, format(scene.start)));
        listen.addEventListener('click', function () { seek(scene.start, true); });
        sec.appendChild(listen);

        body.appendChild(sec);
      });

      if ((lesson.cues || []).length) {
        var transcript = el('div', 'transcript-body');
        transcript.id = 'transcript';
        transcript.hidden = true;
        transcript.appendChild(el('p', 'transcript-hint', '原始转录可能有识别误差。点击任意一段回听。'));
        lesson.cues.forEach(function (cue, i) {
          var b = el('button', 'cue');
          b.id = 'cue-' + i;
          b.appendChild(el('time', null, format(cue.start)));
          b.appendChild(el('span', null, cue.text));
          b.addEventListener('click', function () { seek(cue.start, true); });
          transcript.appendChild(b);
        });
        body.appendChild(transcript);
      }

      var end = el('div', 'reading-end');
      end.appendChild(el('span', null, '— 本次分享结束 —'));
      end.appendChild(el('p', null, '把经验留下，让实践继续。'));
      body.appendChild(end);
      return body;
    }

    /* ---- video binding ---- */

    function bindVideo() {
      video.addEventListener('loadedmetadata', function () {
        if (pendingTime > 0) {
          video.currentTime = pendingTime;
        }
        pendingTime = 0;
      });
      video.addEventListener('error', function () {
        var shell = $('.video-shell');
        if (!shell || $('.video-error')) return;
        var box = el('div', 'video-error');
        box.setAttribute('role', 'alert');
        box.appendChild(document.createTextNode('视频未能加载。'));
        var retry = el('button', null, '重试');
        retry.addEventListener('click', function () { box.remove(); video.load(); });
        box.appendChild(retry);
        shell.appendChild(box);
      });
      video.addEventListener('play', function () { setPlaying(true); });
      video.addEventListener('pause', function () { setPlaying(false); });
      video.addEventListener('timeupdate', function () {
        current = video.currentTime;
        var now = $('#time-now');
        if (now) now.textContent = format(current);
        var pct = $('#reading-pct');
        if (pct && lesson.duration) pct.textContent = Math.min(100, Math.floor(current / lesson.duration * 100)) + '% 已播放';
        var slot = Math.floor(current / 5);
        if (slot !== lastSavedSlot) { write(K_PROGRESS + lesson.id, current); lastSavedSlot = slot; }
        if (following) scrollToActive(false);
      });
      video.addEventListener('seeked', function () {
        current = video.currentTime;
        if (following) scrollToActive(true);
      });
    }

    function setPlaying(value) {
      var dot = $('#status-dot');
      var text = $('#status-text');
      if (dot) dot.classList.toggle('playing', value);
      if (text) text.textContent = value ? '正在播放' : '随时回到现场';
    }

    function setFollowing(value) {
      following = value;
      var cb = $('#follow-toggle');
      if (cb) cb.checked = value;
      syncFollowUI();
    }

    function syncFollowUI() {
      var paused = $('#follow-paused');
      if (paused) paused.hidden = following;
      var text = $('#follow-text');
      if (text) text.textContent = following ? '跟随播放' : '自由阅读';
    }

    function setMode(value) {
      mode = value;
      $$('.mode-tabs button').forEach(function (b, i) {
        b.classList.toggle('selected', (i === 0) === (value === 'notes'));
      });
      var notes = $('#scene-0');
      var transcript = $('#transcript');
      if (notes) notes.hidden = value !== 'notes';
      $$('.scene').forEach(function (s) { s.hidden = value !== 'notes'; });
      var summary = $('.lesson-summary');
      if (summary) summary.hidden = value !== 'notes';
      var intro = $('.reading-intro');
      if (intro) intro.hidden = value !== 'notes';
      var end = $('.reading-end');
      if (end) end.hidden = value !== 'notes';
      if (transcript) transcript.hidden = value !== 'cues';
      var hint = $('#reading-hint');
      if (hint) hint.textContent = value === 'notes' ? '图文按章节定位' : '原话按转录时间定位';
      lastFollowKey = '';
      scrollToActive(true);
    }

    function seek(t, play) {
      if (!video) return;
      var value = clamp(Number(t) || 0, 0, lesson.duration || 0);
      video.currentTime = value;
      current = value;
      if (!following) setFollowing(true);
      scrollToActive(true);
      if (play) {
        var p = video.play();
        if (p && p.catch) p.catch(function () { /* 用户手势限制，忽略 */ });
      }
    }

    function activeIndexFor(time) {
      var scenes = lesson.scenes || [];
      var idx = 0;
      scenes.forEach(function (s, i) { if (time >= s.start) idx = i; });
      return scenes.length ? idx : -1;
    }

    function activeCueFor(time) {
      var cues = lesson.cues || [];
      var lo = 0, hi = cues.length - 1, result = -1;
      while (lo <= hi) {
        var mid = (lo + hi) >> 1;
        if (cues[mid].start <= time) { result = mid; lo = mid + 1; } else hi = mid - 1;
      }
      return result;
    }

    function scrollToActive(force) {
      if (!reading) return;
      var key;
      if (mode === 'notes') {
        var idx = activeIndexFor(current);
        key = 'scene-' + Math.max(0, idx);
        if (idx !== activeIndex) {
          activeIndex = idx;
          $$('.chapter-list button').forEach(function (b) {
            b.classList.toggle('chapter-active', Number(b.dataset.index) === idx);
          });
          $$('.scene').forEach(function (s, i) { s.classList.toggle('is-current', i === idx); });
          var scenes = lesson.scenes || [];
          var counter = $('#chapter-counter');
          if (counter) counter.textContent = pad(Math.max(0, idx + 1)) + ' / ' + pad(scenes.length);
        }
      } else {
        var ci = activeCueFor(current);
        key = 'cue-' + Math.max(0, ci);
        if (ci !== activeIndex) {
          activeIndex = ci;
          $$('.cue').forEach(function (c, i) { c.classList.toggle('is-current', i === ci); });
        }
      }
      if (!force && key === lastFollowKey) return;
      lastFollowKey = key;
      var node = reading.querySelector('#' + key);
      if (!node) return;
      var top = node.getBoundingClientRect().top - reading.getBoundingClientRect().top + reading.scrollTop - 24;
      reading.scrollTo({ top: Math.max(0, top), behavior: reduced ? 'auto' : 'smooth' });
    }

    function updateActive(force) {
      activeIndex = -1;
      scrollToActive(force);
      syncFollowUI();
    }
  }

  function clamp(v, min, max) { return Math.min(max, Math.max(min, v)); }

  /* ==================== bootstrap ==================== */

  document.addEventListener('DOMContentLoaded', function () {
    var page = document.body.getAttribute('data-page');
    if (page === 'archive') initArchive();
    else if (page === 'lesson') initLesson();
  });
})();
