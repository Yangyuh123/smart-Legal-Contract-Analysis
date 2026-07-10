import { defineStore } from 'pinia'
import { ref } from 'vue'
import { reviewApi, type ReviewRecord, type ReviewRisk } from '@/api/reviews'

export const useReviewsStore = defineStore('reviews', () => {
  const reviews = ref<ReviewRecord[]>([])
  const currentReview = ref<ReviewRecord | null>(null)
  const currentRisks = ref<ReviewRisk[]>([])
  const loading = ref(false)
  const total = ref(0)

  /** 获取审查列表 */
  async function fetchReviews(params: { page: number; size: number }): Promise<void> {
    loading.value = true
    try {
      const res = await reviewApi.list(params)
      reviews.value = res.records
      total.value = res.total
    } finally {
      loading.value = false
    }
  }

  /** 获取审查详情 */
  async function fetchReviewById(id: number): Promise<void> {
    loading.value = true
    try {
      const res = await reviewApi.getById(id)
      currentReview.value = res
      currentRisks.value = res?.risks || []
    } finally {
      loading.value = false
    }
  }

  /** 清除当前审查 */
  function clearCurrentReview(): void {
    currentReview.value = null
    currentRisks.value = []
  }

  return {
    reviews, currentReview, currentRisks, loading, total,
    fetchReviews, fetchReviewById, clearCurrentReview,
  }
})
