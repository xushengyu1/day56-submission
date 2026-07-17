import { useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { useNavigate, useParams } from 'react-router-dom'
import { candidatesApi } from '@/api/candidates'
import { claimsApi } from '@/api/claims'

export function OtherClaimForm() {
  const { candidateId = '' } = useParams<{ candidateId: string }>()
  const navigate = useNavigate()
  const [answers, setAnswers] = useState<Record<string, string>>({})
  const candidateQuery = useQuery({
    queryKey: ['candidates', 'detail', candidateId],
    queryFn: () => candidatesApi.get(candidateId),
    enabled: Boolean(candidateId),
  })
  const questionsQuery = useQuery({
    queryKey: ['claims', 'questions', candidateId],
    queryFn: () => claimsApi.questions(candidateId),
    enabled: Boolean(candidateId),
  })
  const submit = useMutation({
    mutationFn: () => claimsApi.verifyAnswers(
      candidateId,
      (questionsQuery.data ?? []).map((question) => ({
        question_id: question.id,
        answer: answers[question.id].trim(),
      })),
    ),
    onSuccess: (outcome) => navigate(`/claims/${encodeURIComponent(outcome.claim_id)}/progress`),
  })

  if (!candidateId) return <div role="alert" className="p-8 text-center">缺少候选编号</div>
  if (candidateQuery.isLoading || questionsQuery.isLoading) return <div className="p-8 text-center">正在加载核验问题...</div>
  if (candidateQuery.isError || questionsQuery.isError || !candidateQuery.data) {
    return <div role="alert" className="p-8 text-center">核验问题加载失败，请稍后重试</div>
  }
  const questions = questionsQuery.data ?? []
  const found = candidateQuery.data.found_record
  const allAnswered = questions.length > 0 && questions.every((question) => answers[question.id]?.trim())

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault()
    if (!allAnswered || submit.isPending) return
    submit.mutate()
  }

  return (
    <div className="max-w-4xl mx-auto p-8">
      <section className="bg-white rounded-2xl border border-gray-100 p-5 mb-6">
        <h2 className="text-xl font-bold">{found.name_public ?? '待认领物品'}</h2>
        <p className="text-sm text-gray-500 mt-1">{found.location_public ?? '地点未填写'} · {found.event_time_public ?? '时间未填写'}</p>
      </section>
      <div className="p-4 bg-blue-50 rounded-xl mb-6">
        <p className="text-sm font-medium text-blue-800">AI 辅助核验</p>
        <p className="text-xs text-blue-600 mt-1">请回答后端根据隐藏特征生成的问题，答案不会作为公开信息展示。</p>
      </div>
      <form onSubmit={handleSubmit}>
        <div className="space-y-4">
          {questions.map((question, index) => (
            <div key={question.id} className="bg-white rounded-2xl border border-gray-100 p-6">
              <label htmlFor={`answer-${question.id}`} className="block font-semibold mb-3">问题 {index + 1}</label>
              <p className="mb-4">{question.question_text}</p>
              <textarea
                id={`answer-${question.id}`}
                rows={3}
                placeholder="请详细描述您记忆中的情况..."
                value={answers[question.id] ?? ''}
                onChange={(event) => setAnswers((current) => ({ ...current, [question.id]: event.target.value }))}
                className="w-full px-4 py-3 border border-gray-200 rounded-xl"
              />
            </div>
          ))}
        </div>
        {questions.length === 0 && <p className="mt-4 text-sm text-gray-500">暂无可用核验问题</p>}
        {submit.isError && <p role="alert" className="mt-4 text-sm text-red-600">核验提交失败，请稍后重试</p>}
        <button type="submit" disabled={!allAnswered || submit.isPending} className="mt-6 w-full py-4 bg-blue-600 disabled:bg-blue-300 text-white font-bold rounded-xl">
          {submit.isPending ? '提交中…' : '提交核验'}
        </button>
      </form>
    </div>
  )
}
