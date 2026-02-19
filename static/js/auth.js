function setAuth(data){
  localStorage.setItem("token", data.token);
  localStorage.setItem("role", data.role);
  localStorage.setItem("name", data.name);
  localStorage.setItem("email", data.email);
}

function getToken(){
  return localStorage.getItem("token");
}

function logout(){
  localStorage.clear();
  window.location.href = "/";
}
