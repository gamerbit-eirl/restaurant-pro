"use client";

const mesas = [
  { id: 1, estado: "libre" },
  { id: 2, estado: "libre" },
  { id: 3, estado: "ocupada" },
  { id: 4, estado: "libre" },
  { id: 5, estado: "ocupada" },
  { id: 6, estado: "libre" },
];

export default function Home() {
  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">Mesas</h1>

      <div className="grid grid-cols-4 gap-4">
        {mesas.map((mesa) => (
          <div
            key={mesa.id}
            className={`p-6 rounded-lg text-center text-white font-bold cursor-pointer ${
              mesa.estado === "libre"
                ? "bg-green-500"
                : "bg-red-500"
            }`}
          >
            {mesa.id}
          </div>
        ))}
      </div>
    </div>
  );
}