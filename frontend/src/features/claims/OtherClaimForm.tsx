import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

const MOCK_QUESTIONS = [
  { id: 'q1', text: '请描述伞套或伞袋上是否有任何特殊标记或文字？', isCritical: true },
  { id: 'q2', text: '伞的把手部分有什么特别之处？请描述其材质、形状或颜色。', isCritical: true },
  { id: 'q3', text: '伞面上除了纯黑色外，是否有其他颜色、图案或品牌标识？', isCritical: false },
]

export function OtherClaimForm() {
  const navigate = useNavigate()
  const [answers, setAnswers] = useState<Record<string, string>>({})

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    navigate('/claims/cl-002/progress')
  }

  const allCriticalAnswered = MOCK_QUESTIONS.filter((q) => q.isCritical).every((q) => (answers[q.id] || '').trim().length > 0)

  return (
    <>
      <div className="bg-white border-b border-gray-100 px-8 py-4">
        <div className="flex items-center gap-3 max-w-3xl mx-auto">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-emerald-500 text-white rounded-full flex items-center justify-center text-sm"><i className="fas fa-check"></i></div>
            <span className="text-sm text-emerald-600">选择候选</span>
          </div>
          <div className="flex-1 h-px bg-emerald-300"></div>
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center text-sm font-bold">2</div>
            <span className="text-sm font-semibold text-blue-600">特征核验</span>
          </div>
          <div className="flex-1 h-px bg-gray-200"></div>
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-gray-200 text-gray-400 rounded-full flex items-center justify-center text-sm font-bold">3</div>
            <span className="text-sm text-gray-400">等待结果</span>
          </div>
        </div>
      </div>

      <div className="flex h-full">
        {/* 左侧：物品信息 */}
        <div className="w-[360px] bg-white border-r border-gray-100 p-6 flex-shrink-0">
          <h3 className="text-sm font-semibold text-gray-500 mb-4">认领物品信息</h3>
          <div className="w-full h-48 bg-gray-100 rounded-xl overflow-hidden mb-4">
            <img src="https://images.unsplash.com/photo-1556306535-0f09a537f0a3?w=360&h=192&fit=crop" alt="物品图片" className="w-full h-full object-cover" />
          </div>
          <div className="space-y-3">
            <div>
              <p className="text-lg font-bold text-gray-900">黑色折叠伞</p>
              <span className="px-2 py-0.5 bg-gray-100 text-gray-600 text-xs rounded-full">其他物品</span>
            </div>
            <div className="flex items-center gap-2 text-sm text-gray-600"><i className="fas fa-clock text-gray-400 w-4"></i><span>7 月 16 日 上午 10:30</span></div>
            <div className="flex items-center gap-2 text-sm text-gray-600"><i className="fas fa-location-dot text-gray-400 w-4"></i><span>教学楼 B 区 2 楼楼梯口</span></div>
          </div>
          <div className="mt-6 p-4 bg-blue-50 rounded-xl">
            <div className="flex items-start gap-3">
              <i className="fas fa-robot text-blue-500 mt-0.5"></i>
              <div>
                <p className="text-sm font-medium text-blue-800">AI 辅助核验</p>
                <p className="text-xs text-blue-600 mt-1 leading-relaxed">以下问题由 AI 根据物品隐藏特征自动生成，请根据您对物品的实际记忆回答。</p>
              </div>
            </div>
          </div>
        </div>

        {/* 右侧：核验问题 */}
        <div className="flex-1 p-8 overflow-y-auto">
          <div className="max-w-2xl mx-auto">
            <h2 className="text-xl font-bold text-gray-900 mb-2">请回答以下问题</h2>
            <p className="text-sm text-gray-500 mb-6">请根据您丢失物品的实际情况作答，回答越详细越好</p>

            <form onSubmit={handleSubmit}>
              <div className="space-y-4 mb-6">
                {MOCK_QUESTIONS.map((q, index) => (
                  <div key={q.id} className="bg-white rounded-2xl border border-gray-100 p-6">
                    <div className="flex items-center gap-2 mb-3">
                      <span className="w-7 h-7 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-sm font-bold">{index + 1}</span>
                      <span className="text-sm font-semibold text-gray-500">问题 {index + 1}{q.isCritical ? '（关键）' : ''}</span>
                    </div>
                    <p className="text-base font-medium text-gray-900 mb-4">{q.text}</p>
                    <textarea
                      rows={3}
                      placeholder="请详细描述您记忆中的情况..."
                      value={answers[q.id] || ''}
                      onChange={(e) => setAnswers((prev) => ({ ...prev, [q.id]: e.target.value }))}
                      className="w-full px-4 py-3 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                    />
                  </div>
                ))}
              </div>

              <div className="p-4 bg-amber-50 rounded-xl mb-6">
                <div className="flex items-start gap-3">
                  <i className="fas fa-lightbulb text-amber-500 mt-0.5"></i>
                  <div>
                    <p className="text-sm font-medium text-amber-800">回答提示</p>
                    <p className="text-xs text-amber-700 mt-1">请尽量提供具体的细节描述。系统将通过 AI 语义比对验证您的回答，措辞不同但含义正确也会被识别为匹配。</p>
                  </div>
                </div>
              </div>

              <div className="flex gap-4">
                <button
                  type="submit"
                  disabled={!allCriticalAnswered}
                  className="flex-1 py-4 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white font-bold rounded-xl transition-colors shadow-lg shadow-blue-600/25 text-base"
                >
                  <i className="fas fa-paper-plane mr-2"></i>提交核验
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </>
  )
}
