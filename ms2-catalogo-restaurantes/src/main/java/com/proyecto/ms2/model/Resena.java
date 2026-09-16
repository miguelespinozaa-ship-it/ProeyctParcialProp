package com.proyecto.ms2.model;

import java.time.Instant;

import org.springframework.data.mongodb.core.mapping.Field;

import com.fasterxml.jackson.annotation.JsonProperty;

public class Resena {
    // @Field controla el nombre en MongoDB, @JsonProperty el nombre en el JSON REST (Jackson no lee @Field).
    @Field("usuario_id")
    @JsonProperty("usuario_id")
    private Integer usuarioId;
    private String comentario;
    private int puntuacion;
    private Instant fecha;

    public Integer getUsuarioId() { return usuarioId; }
    public void setUsuarioId(Integer usuarioId) { this.usuarioId = usuarioId; }
    public String getComentario() { return comentario; }
    public void setComentario(String comentario) { this.comentario = comentario; }
    public int getPuntuacion() { return puntuacion; }
    public void setPuntuacion(int puntuacion) { this.puntuacion = puntuacion; }
    public Instant getFecha() { return fecha; }
    public void setFecha(Instant fecha) { this.fecha = fecha; }
}
