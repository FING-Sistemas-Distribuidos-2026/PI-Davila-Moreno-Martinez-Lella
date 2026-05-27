package com.wandanara.backend_api.entity;

import jakarta.persistence.*;
import java.time.LocalDateTime;

@Entity
@Table(name = "searches")
public class Search {

    @Id
    private String id;

    private String query;

    private String status;

    private LocalDateTime createdAt;

    public Search() {
    }

    public Search(String id, String query, String status, LocalDateTime createdAt) {
        this.id = id;
        this.query = query;
        this.status = status;
        this.createdAt = createdAt;
    }

    public String getId() {
        return id;
    }

    public String getQuery() {
        return query;
    }

    public String getStatus() {
        return status;
    }

    public LocalDateTime getCreatedAt() {
        return createdAt;
    }

    public void setId(String id) {
        this.id = id;
    }

    public void setQuery(String query) {
        this.query = query;
    }

    public void setStatus(String status) {
        this.status = status;
    }

    public void setCreatedAt(LocalDateTime createdAt) {
        this.createdAt = createdAt;
    }
}
