import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
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

  {
    path: '/',
    component: () => import('@/layouts/DefaultLayout.vue'),
    meta: { requiresAuth: true },
    children: [
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

      {
        path: 'generate',
        name: 'Generate',
        component: () => import('@/views/generation/GenerationChatView.vue'),
        meta: { title: '合同生成', icon: 'EditPen' },
      },

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

      {
        path: 'compliance/create',
        name: 'ComplianceCreate',
        component: () => import('@/views/compliance/ComplianceCheckView.vue'),
        meta: { title: '合规检查', icon: 'ShieldCheckmark' },
      },
      {
        path: 'compliance/:id',
        name: 'ComplianceResult',
        component: () => import('@/views/compliance/ComplianceResultView.vue'),
        meta: { title: '检查结果' },
      },
      {
        path: 'compliance/history',
        name: 'ComplianceHistory',
        component: () => import('@/views/compliance/ComplianceHistoryView.vue'),
        meta: { title: '检查历史', icon: 'Timer' },
      },

      {
        path: 'notifications',
        name: 'Notifications',
        component: () => import('@/views/notifications/NotificationListView.vue'),
        meta: { title: '消息通知', icon: 'Bell' },
      },
    ],
  },

  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/auth/LoginView.vue'),
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, _from, next) => {
  if (to.meta?.title && typeof to.meta.title === 'string') {
    document.title = `${to.meta.title} - SmartLegal`
  }

  const requiresAuth = to.meta?.requiresAuth === true
  const accessToken = localStorage.getItem('access_token')

  if (requiresAuth && !accessToken) {
    next({
      path: '/auth/login',
      query: { redirect: to.fullPath !== '/' ? to.fullPath : undefined },
      replace: true,
    })
    return
  }

  if (to.path.startsWith('/auth') && accessToken) {
    next({ path: '/dashboard', replace: true })
    return
  }

  next()
})

export default router