package main

import (
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"net/url"
	"os"
	"strconv"

	"github.com/joho/godotenv"
)

func readAPIKey() string {
	err := godotenv.Load()
	if err != nil {
		log.Fatal("Error loading .env file")
	}
	return os.Getenv("GITHUB_API_KEY")
}

func getRepos(client *http.Client, api_key string, since int) ([]Repository, error) {
	baseURL := "https://api.github.com/repositories"

	u, err := url.Parse(baseURL)
	if err != nil {
		return nil, fmt.Errorf("Error parsing URL: %v", err)
	}

	q := u.Query()
	q.Add("since", strconv.Itoa(since))
	u.RawQuery = q.Encode()

	req, err := http.NewRequest("GET", u.String(), nil)
	if err != nil {
		return nil, fmt.Errorf("Error creating request: %v", err)
	}

	req.Header.Add("Accept", "application/vnd.github+json")
	req.Header.Add("Authorization", "Bearer "+api_key)
	req.Header.Add("X-GitHub-Api-Version", "2022-11-28")

	resp, err := client.Do(req)
	if err != nil {
		return nil, fmt.Errorf("Error executing request: %v", err)
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("Error reading response body: %v", err)
	}

	var repositories []Repository
	err = json.Unmarshal(body, &repositories)
	if err != nil {
		return nil, fmt.Errorf("Error unmarshaling JSON: %v", err)
	}

	return repositories, nil
}

func main() {
	api_key := readAPIKey()
	client := &http.Client{}

  since := 0
  num_found := 0

  for i := 0; i < 100; i++ {
    repos, err := getRepos(client, api_key, since)
    if err != nil {
      fmt.Printf("Error getting repos: %v\n", err)
      return
    }

    num_found += len(repos)
    fmt.Printf("%d\n", num_found)
    since = repos[len(repos)-1].ID
  }
}
