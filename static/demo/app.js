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

loadUsers();
