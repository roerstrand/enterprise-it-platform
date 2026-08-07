async function loadUsers() {
  const list = document.getElementById("user-list");
  const error = document.getElementById("error");
  list.innerHTML = "";
  error.textContent = "";

  try {
    const res = await fetch("/demo/api/users");
    if (!res.ok) throw new Error("gRPC service is down");
    const users = await res.json();
    for (const u of users) {
      const li = document.createElement("li");
      li.textContent = `${u.id}: ${u.name} (${u.email})`;
      list.appendChild(li);
    }
  } catch (e) {
    error.textContent = e.message;
  }
}

document.getElementById("create-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const name = document.getElementById("name").value;
  const email = document.getElementById("email").value;
  const password = document.getElementById("password").value;
  const error = document.getElementById("error");

  try {
    const res = await fetch("/demo/api/users", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, email, password }),
    });
    if (!res.ok) throw new Error("gRPC service is down");
    e.target.reset();
    await loadUsers();
  } catch (err) {
    error.textContent = err.message;
  }
});

document.getElementById("login-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const email = document.getElementById("login-email").value;
  const password = document.getElementById("login-password").value;
  const status = document.getElementById("login-status");

  try {
    const res = await fetch("/demo/api/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    if (!res.ok) throw new Error("Invalid email or passowrd");
    const data = await res.json();
    localStorage.setItem("access_token", data.access_token);
    status.textContent = "Logged in";
    e.target.reset();
  } catch (err) {
    status.textContent = err.message;
  }
});

loadUsers();

async function loadIncidents() {
  const list = document.getElementById("incident-list");
  const error = document.getElementById("incident-error");
  list.innerHTML = "";
  error.textContent = "";

  try {
    const res = await fetch("/demo/api/incidents");
    if (!res.ok) throw new Error("gRPC service is down");
    const incidents = await res.json();
    for (const i of incidents) {
      const tr = document.createElement("tr");
      const cells = [
        i.id,
        i.title,
        i.status,
        i.severity,
        i.ai_suggested_severity || "—",
        i.ai_suggested_status || "—",
        i.ai_summary || "—",
      ];
      for (const value of cells) {
        const td = document.createElement("td");
        td.textContent = value;
        tr.appendChild(td);
      }
      list.appendChild(tr);
    }
  } catch (e) {
    error.textContent = e.message;
  }
}

document
  .getElementById("refresh-incidents")
  .addEventListener("click", loadIncidents);

document
  .getElementById("incident-create-form")
  .addEventListener("submit", async (e) => {
    e.preventDefault();
    const title = document.getElementById("incident-title").value;
    const description = document.getElementById("incident-description").value;
    const severity = document.getElementById("incident-severity").value;
    const ci_id = parseInt(document.getElementById("incident-ci-id").value, 10);
    const error = document.getElementById("incident-error");

    try {
      const res = await fetch("/demo/api/incidents", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title, description, severity, ci_id }),
      });
      if (!res.ok) throw new Error("gRPC service is down");
      e.target.reset();
      await loadIncidents();
    } catch (err) {
      error.textContent = err.message;
    }
  });

document
  .getElementById("incident-update-form")
  .addEventListener("submit", async (e) => {
    e.preventDefault();
    const incidentId = document.getElementById("update-incident-id").value;
    const text = document.getElementById("update-text").value;
    const error = document.getElementById("incident-error");

    try {
      const res = await fetch(`/demo/api/incidents/${incidentId}/updates`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text }),
      });
      if (!res.ok) throw new Error("gRPC service is down");
      e.target.reset();
      await loadIncidents();
    } catch (err) {
      error.textContent = err.message;
    }
  });

loadIncidents();
