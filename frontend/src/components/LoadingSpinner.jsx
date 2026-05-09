export default function LoadingSpinner({ message = "Loading...", size = "md" }) {
  const sizes = { sm: "w-6 h-6", md: "w-10 h-10", lg: "w-16 h-16" }
  return (
    <div className="flex flex-col items-center justify-center gap-4 py-16">
      <div className={`${sizes[size]} border-2 border-neon border-t-transparent rounded-full animate-spin`} />
      <p className="text-slate-400 text-sm animate-pulse">{message}</p>
    </div>
  )
}
