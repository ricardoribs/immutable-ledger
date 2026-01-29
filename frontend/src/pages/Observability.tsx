export default function Observability() {
  const tools = [
    { name: 'Grafana', url: 'http://localhost:3000' },
    { name: 'Prometheus', url: 'http://localhost:9090' },
    { name: 'Alertmanager', url: 'http://localhost:9093' },
    { name: 'Kibana', url: 'http://localhost:5601' },
    { name: 'Jaeger', url: 'http://localhost:16686' },
  ];

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-brand-dark">Observabilidade</h1>
      <section className="lb-card lb-card-info p-4">
        <h2 className="font-semibold mb-3">Ferramentas</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {tools.map((tool) => (
            <a
              key={tool.name}
              href={tool.url}
              target="_blank"
              rel="noreferrer"
              className="flex items-center justify-between border border-slate-100 rounded-xl px-4 py-3 hover:bg-brand-light"
            >
              <span className="font-semibold text-brand-ink">{tool.name}</span>
              <span className="text-xs text-slate-500">Abrir</span>
            </a>
          ))}
        </div>
      </section>
    </div>
  );
}

