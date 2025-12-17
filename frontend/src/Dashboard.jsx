export default function Dashboard({ summary }) {
  return (
    <div className="p-6">
      <h1>Total Cost: ${summary.total}</h1>
      <h2>AWS: ${summary.aws}</h2>
      <h2>Azure: ${summary.azure}</h2>
    </div>
  );
}
