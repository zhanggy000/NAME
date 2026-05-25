export default function AboutPage() {
  return (
    <article className="prose dark:prose-invert max-w-none">
      <h1 className="font-serif-cn">关于 NAME</h1>

      <p className="lead text-stone-500">
        一套综合中国传统命理、文化典籍与现代 AI 复审的取名工具。每个名字都可解释、可溯源。
      </p>

      <h2 className="font-serif-cn mt-8">核心理念</h2>
      <blockquote className="font-serif-cn text-xl border-l-4 border-stone-300 pl-4">
        八字定方向，字义定气质，五格守底线。
      </blockquote>

      <h2 className="font-serif-cn mt-8">五维评分体系</h2>
      <table>
        <thead>
          <tr><th>维度</th><th>权重</th><th>作用</th></tr>
        </thead>
        <tbody>
          <tr><td>八字补益</td><td>30%</td><td>灵魂 · 决定方向</td></tr>
          <tr><td>三才五格</td><td>25%</td><td>避坑 · 决定下限</td></tr>
          <tr><td>字义寓意</td><td>20%</td><td>气质 · 决定格调</td></tr>
          <tr><td>音律读音</td><td>15%</td><td>日常 · 决定使用体验</td></tr>
          <tr><td>字形书写</td><td>10%</td><td>美观 · 决定第一印象</td></tr>
        </tbody>
      </table>

      <h2 className="font-serif-cn mt-8">和市面工具的差异</h2>
      <ul>
        <li><strong>康熙繁体笔画</strong>：所有数理计算用康熙笔画，不用简体（市面常见错误）</li>
        <li><strong>用神而非缺啥补啥</strong>：严格按调候 → 扶抑 → 通关 → 病药四步走</li>
        <li><strong>典籍可溯源</strong>：每个推荐字都标明出自哪本经典哪句</li>
        <li><strong>名人有参照</strong>：每个字附带历史/现代同字名人</li>
        <li><strong>评分可解释</strong>：每一分都拆解到具体规则，不是黑盒</li>
      </ul>

      <h2 className="font-serif-cn mt-8">开源</h2>
      <p>
        项目代码与文档完全开源：
        <a href="https://github.com/zhanggy000/NAME" target="_blank" rel="noreferrer">
          github.com/zhanggy000/NAME
        </a>
      </p>
    </article>
  );
}
