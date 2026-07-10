import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  // ---- Auth routes (no auth required) ----
  {
    path: '/auth',
    component: () => import('@/layouts/AuthLayout.vue'),
    children: [
      {
        path: 'login',
        name: 'Login',
        component: () => import('@/views/auth/LoginView.vue'),
        meta: { title: '登录' },
      },
      {
        path: 'register',
        name: 'Register',
        component: () => import('@/views/auth/RegisterView.vue'),
        meta: { title: '注册' },
      },
    ],
  },

  // ---- Protected routes (requires auth) ----
  {
    path: '/',
    component: () => import('@/layouts/DefaultLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      // 仪表盘
      {
        path: '',
        redirect: '/dashboard',
      },
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/dashboard/DashboardView.vue'),
        meta: { title: '仪表盘', icon: 'Odometer' },
      },

      // 合同审查
      {
        path: 'review/create',
        name: 'ReviewCreate',
        component: () => import('@/views/review/ReviewCreateView.vue'),
        meta: { title: '创建审查', icon: 'Checked' },
      },
      {
        path: 'review/:id',
        name: 'ReviewResult',
        component: () => import('@/views/review/ReviewResultView.vue'),
        meta: { title: '审查结果' },
      },
      {
        path: 'review/history',
        name: 'ReviewHistory',
        component: () => import('@/views/review/ReviewHistoryView.vue'),
        meta: { title: '审查历史', icon: 'Timer' },
      },

      // 合同生成
      {
        path: 'generate',
        name: 'Generate',
        component: () => import('@/views/generation/GenerationChatView.vue'),
        meta: { title: '合同生成', icon: 'EditPen' },
      },

      // 合同比对
      {
        path: 'compare',
        name: 'ComparisonCreate',
        component: () => import('@/views/comparison/ComparisonCreateView.vue'),
        meta: { title: '合同比对', icon: 'Switch' },
      },
      {
        path: 'compare/:id',
        name: 'ComparisonResult',
        component: () => import('@/views/comparison/ComparisonResultView.vue'),
        meta: { title: '比对结果' },
      },

      // 知识库
      {
        path: 'knowledge',
        name: 'KnowledgeDocs',
        component: () => import('@/views/knowledge/KnowledgeDocumentView.vue'),
        meta: { title: '知识库', icon: 'Reading' },
      },
      {
        path: 'knowledge/qa',
        name: 'KnowledgeQA',
        component: () => import('@/views/knowledge/KnowledgeQAView.vue'),
        meta: { title: '知识问答', icon: 'ChatDotRound' },
      },

      // 通知
      {
        path: 'notifications',
        name: 'Notifications',
        component: () => import('@/views/notifications/NotificationListView.vue'),
        meta: { title: '消息通知', icon: 'Bell' },
      },
    ],
  },

  // ---- 404 fallback ----
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/auth/LoginView.vue'),
  },
]

// ---- 创建路由实例 ----

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// ---- 全局前置守卫 ----

router.beforeEach((to, _from, next) => {
  // 设置页面标题
  if (to.meta?.title && typeof to.meta.title === 'string') {
    document.title = `${to.meta.title} - SmartLegal`
  }

  const requiresAuth = to.meta?.requiresAuth === true
  const accessToken = localStorage.getItem('access_token')

  if (requiresAuth && !accessToken) {
    // 需要登录但未登录 → 跳转登录页，并带上原始目标以便登录后回跳
    next({
      path: '/auth/login',
      query: { redirect: to.fullPath !== '/' ? to.fullPath : undefined },
      replace: true,
    })
    return
  }

  if (to.path.startsWith('/auth') && accessToken) {
    // 已登录却访问登录/注册页 → 重定向到仪表盘
    next({ path: '/dashboard', replace: true })
    return
  }

  next()
})

export default router
