package com.wandanara.backend_api.entity;

import jakarta.persistence.*;

@Entity
@Table(name = "search_results")
public class SearchResult {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private String searchId;

    private String store;

    private String name;

    private Integer price;

    private String url;

    public SearchResult() {
    }

    public SearchResult(String searchId, String store, String name, Integer price, String url) {
        this.searchId = searchId;
        this.store = store;
        this.name = name;
        this.price = price;
        this.url = url;
    }

    public Long getId() {
        return id;
    }

    public String getSearchId() {
        return searchId;
    }

    public String getStore() {
        return store;
    }

    public String getName() {
        return name;
    }

    public Integer getPrice() {
        return price;
    }

    public String getUrl() {
        return url;
    }

    public void setId(Long id) {
        this.id = id;
    }

    public void setSearchId(String searchId) {
        this.searchId = searchId;
    }

    public void setStore(String store) {
        this.store = store;
    }

    public void setName(String name) {
        this.name = name;
    }

    public void setPrice(Integer price) {
        this.price = price;
    }

    public void setUrl(String url) {
        this.url = url;
    }
}