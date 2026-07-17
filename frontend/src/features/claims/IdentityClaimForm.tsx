import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

export function IdentityClaimForm() {
  const navigate = useNavigate()
  const [idNumber, setIdNumber] = useState('')
  const maxAttempts = 2
  const remainingAttempts = 2

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (idNumber.length !== 18) return
    // Mock: 验证通过后跳转到进度页
    navigate('/claims/cl-001/progress')
  }

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
            <span className="text-sm font-semibold text-blue-600">身份核验</span>
          </div>
          <div className="flex-1 h-px bg-gray-200"></div>
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-gray-200 text-gray-400 rounded-full flex items-center justify-center text-sm font-bold">3</div>
            <span className="text-sm text-gray-400">等待交接</span>
          </div>
        </div>
      </div>

      <div className="flex items-center justify-center h-full">
        <div className="w-[560px]">
          <div className="text-center mb-8">
            <div className="w-20 h-20 bg-blue-50 rounded-full flex items-center justify-center mx-auto mb-4">
              <i className="fas fa-shield-halved text-blue-600 text-3xl"></i>
            </div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">身份证件号码核验</h2>
            <p className="text-gray-500">请输入您的完整身份证号码以验证身份</p>
          </div>

          <div className="bg-white rounded-2xl border border-gray-100 p-5 mb-6">
            <div className="flex items-center gap-4">
              <div className="w-16 h-16 rounded-xl bg-gray-100 overflow-hidden flex items-center justify-center">
                <i className="fas fa-id-card text-gray-400 text-2xl"></i>
              </div>
              <div className="flex-1">
                <h3 className="font-bold text-gray-900">居民身份证</h3>
                <p className="text-sm text-gray-500">拾得于 食堂一楼 · 7月15日</p>
              </div>
              <div className="text-right">
                <p className="text-xs text-gray-400">证件号码（掩码）</p>
                <p className="text-lg font-mono font-bold text-gray-700">110***********1234</p>
              </div>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="bg-white rounded-2xl border border-gray-100 p-6 mb-6">
            <label className="block text-sm font-semibold text-gray-900 mb-3">请输入完整证件号码</label>
            <div className="relative">
              <i className="fas fa-id-card absolute left-4 top-1/2 -translate-y-1/2 text-gray-400"></i>
              <input
                type="text"
                placeholder="请输入 18 位身份证号码"
                maxLength={18}
                value={idNumber}
                onChange={(e) => setIdNumber(e.target.value.replace(/\s/g, ''))}
                className="w-full pl-11 pr-4 py-4 border-2 border-gray-200 rounded-xl text-lg font-mono tracking-wider focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div className="flex items-center justify-between mt-3">
              <p className="text-xs text-gray-400"><i className="fas fa-lock mr-1"></i>号码将通过加密方式比对，不会明文存储</p>
              <p className="text-xs text-gray-400">剩余尝试：<span className="font-semibold text-amber-600">{remainingAttempts}</span> 次</p>
            </div>
          </form>

          <div className="p-4 bg-amber-50 rounded-xl mb-6">
            <div className="flex items-start gap-3">
              <i className="fas fa-exclamation-triangle text-amber-500 mt-0.5"></i>
              <div>
                <p className="text-sm font-medium text-amber-800">安全说明</p>
                <ul className="text-xs text-amber-700 mt-1 space-y-1 list-disc list-inside">
                  <li>同一账号最多尝试 {maxAttempts} 次，超限后需申请管理员复核</li>
                  <li>验证失败不会提示具体错误位置</li>
                  <li>号码仅用于一次精确比对，不会被记录到日志中</li>
                </ul>
              </div>
            </div>
          </div>

          <div className="flex gap-4">
            <button
              onClick={handleSubmit}
              disabled={idNumber.length !== 18}
              className="flex-1 py-4 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white font-bold rounded-xl transition-colors shadow-lg shadow-blue-600/25 text-base"
            >
              <i className="fas fa-check-circle mr-2"></i>提交验证
            </button>
          </div>
        </div>
      </div>
    </>
  )
}
