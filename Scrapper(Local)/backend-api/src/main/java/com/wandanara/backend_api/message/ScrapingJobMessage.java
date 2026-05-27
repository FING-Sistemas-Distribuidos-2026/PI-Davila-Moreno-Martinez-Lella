package com.wandanara.backend_api.message;

public class ScrapingJobMessage {

    private String searchId;
    private String query;
    private String store;
    private Integer attempts;

    public ScrapingJobMessage() {
    }

    public ScrapingJobMessage(String searchId, String query, String store, Integer attempts) {
        this.searchId = searchId;
        this.query = query;
        this.store = store;
        this.attempts = attempts;
    }

    public String getSearchId() {
        return searchId;
    }

    public void setSearchId(String searchId) {
        this.searchId = searchId;
    }

    public String getQuery() {
        return query;
    }

    public void setQuery(String query) {
        this.query = query;
    }

    public String getStore() {
        return store;
    }

    public void setStore(String store) {
        this.store = store;
    }
}