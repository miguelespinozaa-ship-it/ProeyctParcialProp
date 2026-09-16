package com.proyecto.ms2.security;

public class AuthenticatedUser {
    private final Integer userId;
    private final String rol;
    private final String restauranteId;

    public AuthenticatedUser(Integer userId, String rol, String restauranteId) {
        this.userId = userId;
        this.rol = rol;
        this.restauranteId = restauranteId;
    }

    public Integer getUserId() { return userId; }
    public String getRol() { return rol; }
    public String getRestauranteId() { return restauranteId; }

    public boolean isAdmin() { return "admin".equals(rol); }
}
