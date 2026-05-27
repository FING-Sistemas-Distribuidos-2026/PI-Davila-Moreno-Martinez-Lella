package com.wandanara.backend_api.message;

import java.util.List;

public class ScrapingResultMessage {

    private String searchId;
    private String store;
    private String status;
    private List<ProductResult> results;

    public ScrapingResultMessage() {
    }

    public ScrapingResultMessage(String searchId, String store, String status, List<ProductResult> results) {
        this.searchId = searchId;
        this.store = store;
        this.status = status;
        this.results = results;
    }

    public String getSearchId() {
        return searchId;
    }

    public String getStore() {
        return store;
    }

    public String getStatus() {
        return status;
    }

    public List<ProductResult> getResults() {
        return results;
    }

    public void setSearchId(String searchId) {
        this.searchId = searchId;
    }

    public void setStore(String store) {
        this.store = store;
    }

    public void setStatus(String status) {
        this.status = status;
    }

    public void setResults(List<ProductResult> results) {
        this.results = results;
    }
}
