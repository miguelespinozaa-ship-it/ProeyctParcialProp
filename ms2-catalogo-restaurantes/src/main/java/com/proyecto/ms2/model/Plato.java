package com.proyecto.ms2.model;

import org.springframework.data.mongodb.core.mapping.Field;

public class Plato {
    // Fuerza el nombre "id" en Mongo; sin esto Spring Data lo guarda como "_id".
    @Field("id")
    private String id;
    private String nombre;
    private String descripcion;
    private double precio;
    private String categoria;
    private boolean disponible;

    public String getId() { return id; }
    public void setId(String id) { this.id = id; }
    public String getNombre() { return nombre; }
    public void setNombre(String nombre) { this.nombre = nombre; }
    public String getDescripcion() { return descripcion; }
    public void setDescripcion(String descripcion) { this.descripcion = descripcion; }
    public double getPrecio() { return precio; }
    public void setPrecio(double precio) { this.precio = precio; }
    public String getCategoria() { return categoria; }
    public void setCategoria(String categoria) { this.categoria = categoria; }
    public boolean isDisponible() { return disponible; }
    public void setDisponible(boolean disponible) { this.disponible = disponible; }
}
