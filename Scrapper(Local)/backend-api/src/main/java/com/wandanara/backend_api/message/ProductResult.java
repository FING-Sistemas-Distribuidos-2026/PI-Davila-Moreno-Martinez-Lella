package com.wandanara.backend_api.message;

public class ProductResult {

    private String name;
    private Integer price;
    private String url;

    public ProductResult() {
    }

    public ProductResult(String name, Integer price, String url) {
        this.name = name;
        this.price = price;
        this.url = url;
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