// =========================================================
// init.js  —  Inicialización de MongoDB (inventario-db)
//
// Crea la coleccion "hardware" con validador de esquema,
// inserta los documentos desde seeds/hardware.json y
// crea indices para optimizar las busquedas.
//
// =========================================================

const db = db.getSiblingDB("inventario");

// ---------- Coleccion con validador flexible ----------
db.createCollection("hardware", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["equipo_id"],
      properties: {
        equipo_id: { bsonType: "string",
                     description: "ID compartido con SQL Server (ej: PC-0001)" }
      }
    }
  }
});

// ---------- Indices ----------
db.hardware.createIndex({ equipo_id: 1 }, { unique: true });
// tipo: filtrado frecuente (desktop / laptop / servidor)
db.hardware.createIndex({ tipo: 1 });

// ---------- Datos iniciales (seeds/hardware.json) ----------
const docs = [
  { equipo_id:"PC-0001", tipo:"desktop", fabricante:"Lenovo",
    modelo:"ThinkCentre M75q", cpu:"AMD Ryzen 5 PRO 4650GE @ 3.3GHz",
    ram_gb:16, disco_gb:512, disco_tipo:"ssd",
    so:"Windows 11 Pro 23H2",
    monitor:"Samsung 24\" Full HD", mouse:true, teclado:true },
  { equipo_id:"PC-0002", tipo:"laptop", fabricante:"HP",
    modelo:"EliteBook 840 G9", cpu:"Intel Core i5-1235U @ 1.3GHz",
    ram_gb:8, disco_gb:256, disco_tipo:"nvme",
    so:"Windows 11 Pro 23H2",
    monitor:"N/A (laptop)", mouse:false, teclado:true, bateria_salud_pct:92 },
  { equipo_id:"PC-0003", tipo:"desktop", fabricante:"Dell",
    modelo:"OptiPlex 3080", cpu:"Intel Core i5-10500 @ 3.1GHz",
    ram_gb:16, disco_gb:1024, disco_tipo:"ssd", so:"Ubuntu 22.04 LTS",
    monitor:"Dell E2220", mouse:true, teclado:true },
  { equipo_id:"PC-0004", tipo:"laptop", fabricante:"Lenovo",
    modelo:"V14 G2", cpu:"AMD Ryzen 5 5500U @ 2.1GHz",
    ram_gb:8, disco_gb:256, disco_tipo:"ssd", so:"Windows 11 Home",
    monitor:"N/A (laptop)", mouse:true, teclado:true, bateria_salud_pct:78 },
  { equipo_id:"PC-0005", tipo:"desktop", fabricante:"HP",
    modelo:"EliteDesk 800 G5", cpu:"Intel Core i7-9700 @ 3.0GHz",
    ram_gb:16, disco_gb:512, disco_tipo:"ssd", so:"Windows 11 Pro",
    monitor:"HP E243", mouse:true, teclado:true },
  { equipo_id:"PC-0006", tipo:"desktop", fabricante:"ASUS",
    modelo:"ExpertCenter D500", cpu:"Intel Core i5-11400 @ 2.6GHz",
    ram_gb:32, disco_gb:1024, disco_tipo:"nvme", so:"Windows 11 Pro",
    gpu:"NVIDIA GTX 1650", monitor:"ASUS VA24", mouse:true, teclado:true },
  { equipo_id:"PC-0007", tipo:"laptop", fabricante:"Dell",
    modelo:"Latitude 3420", cpu:"Intel Core i5-1135G7 @ 2.4GHz",
    ram_gb:8, disco_gb:256, disco_tipo:"ssd", so:"Windows 10 Pro",
    monitor:"N/A (laptop)", mouse:false, teclado:true, bateria_salud_pct:85 },
  { equipo_id:"PC-0008", tipo:"desktop", fabricante:"Lenovo",
    modelo:"ThinkCentre M70s", cpu:"Intel Core i5-10400 @ 2.9GHz",
    ram_gb:16, disco_gb:512, disco_tipo:"ssd", so:"Fedora 39",
    monitor:"Lenovo L24", mouse:true, teclado:true },
  { equipo_id:"PC-0009", tipo:"servidor", fabricante:"HP",
    modelo:"ProDesk 600 G6", cpu:"Intel Core i7-10700 @ 2.9GHz",
    ram_gb:32, disco_gb:1024, disco_tipo:"ssd",
    so:"Windows Server 2022", rol:"Servidor de practicas BD",
    monitor:"HP P24", mouse:true, teclado:true },
  { equipo_id:"PC-0010", tipo:"laptop", fabricante:"ASUS",
    modelo:"Vivobook Pro 15", cpu:"AMD Ryzen 7 5800H @ 3.2GHz",
    ram_gb:16, disco_gb:512, disco_tipo:"nvme", so:"Windows 11 Home",
    gpu:"NVIDIA RTX 3050", monitor:"N/A (laptop)",
    mouse:true, teclado:true, bateria_salud_pct:96 },
  { equipo_id:"PC-0011", tipo:"desktop", fabricante:"Dell",
    modelo:"OptiPlex 7010 (legacy)", cpu:"Intel Core i3-3220 @ 3.3GHz",
    ram_gb:4, disco_gb:500, disco_tipo:"hdd", so:"Sin SO (baja)",
    monitor:"Dell E1912", mouse:false, teclado:false },
  { equipo_id:"PC-0012", tipo:"servidor", fabricante:"Lenovo",
    modelo:"ThinkStation P340", cpu:"Intel Xeon W-1250 @ 3.3GHz",
    ram_gb:64, disco_gb:2048, disco_tipo:"nvme",
    so:"Ubuntu Server 22.04", gpu:"NVIDIA Quadro P620",
    monitor:"Lenovo T27", mouse:true, teclado:true }
];

db.hardware.insertMany(docs);
print("Coleccion 'hardware' creada con " + db.hardware.countDocuments() + " documentos.");
