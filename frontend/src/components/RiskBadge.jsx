export default function RiskBadge({ decision, size = "md" }) {
  const sizes = {
    sm: "text-xs px-2 py-0.5",
    md: "text-xs px-3 py-1",
    lg: "text-sm px-4 py-1.5",
  }
  const styles = {
    APPROVE: "badge-approve",
    REJECT: "badge-reject",
    REVIEW: "badge-review",
  }
  return (
    <span className={`rounded-full font-bold ${sizes[size]} ${styles[decision] || 'badge-review'}`}>
      {decision}
    </span>
  )
}
