package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"github.com/joho/godotenv"
	"io"
	"log"
	"net/http"
	"os"
	"time"

	"github.com/aws/aws-sdk-go/aws"
	"github.com/aws/aws-sdk-go/aws/credentials"
	"github.com/aws/aws-sdk-go/aws/session"
	"github.com/aws/aws-sdk-go/service/s3"
)

// Initialize S3 client
func createS3Client() *s3.S3 {
	sess := session.Must(session.NewSession(&aws.Config{
		Region:      aws.String("us-east-2"), // Replace with your AWS region
		Credentials: credentials.NewEnvCredentials(),
	}))
	return s3.New(sess)
}

type PaginationState struct {
	LastPage int `json:"last_page"`
}

const stateFilePath = "pagination_state.json"

// LoadState loads the last saved page number from the JSON file
func LoadState() (PaginationState, error) {
	var state PaginationState
	file, err := os.Open(stateFilePath)
	if err != nil {
		if os.IsNotExist(err) {
			return PaginationState{LastPage: 1}, nil // Start from page 1 if no state file exists
		}
		return state, err
	}
	defer file.Close()

	decoder := json.NewDecoder(file)
	err = decoder.Decode(&state)
	if err != nil {
		return state, err
	}
	return state, nil
}

// SaveState saves the last page number to the JSON file
func SaveState(state PaginationState) error {
	file, err := os.Create(stateFilePath)
	if err != nil {
		return err
	}
	defer file.Close()

	encoder := json.NewEncoder(file)
	return encoder.Encode(state)
}

func readAPIKey() string {
	err := godotenv.Load("githubAccess.env")
	if err != nil {
		log.Fatal("Error loading .env file")
	}
	return os.Getenv("GITHUB_API_KEY")
}

func fetchRepositories() []Repository {
	apiKey := readAPIKey()
	client := &http.Client{}

	// Load the last page from the previous session
	state, err := LoadState()
	if err != nil {
		log.Fatalf("Error loading state: %v", err)
	}

	var allRepositories []Repository
	page := state.LastPage
	perPage := 100

	for {
		// Update URL with pagination parameters
		url := fmt.Sprintf("https://api.github.com/repositories?page=%d&per_page=%d", page, perPage)
		req, err := http.NewRequest("GET", url, nil)
		if err != nil {
			log.Fatalf("Error creating request: %v", err)
		}

		// Set headers
		req.Header.Add("Accept", "application/vnd.github+json")
		req.Header.Add("Authorization", "Bearer "+apiKey)
		req.Header.Add("X-GitHub-Api-Version", "2022-11-28")

		resp, err := client.Do(req)
		if err != nil {
			log.Fatalf("Error executing request: %v", err)
		}
		defer resp.Body.Close()

		body, err := io.ReadAll(resp.Body)
		if err != nil {
			log.Fatalf("Error reading response body: %v", err)
		}

		var repositories []Repository
		err = json.Unmarshal(body, &repositories)
		if err != nil {
			log.Fatalf("Error unmarshaling JSON: %v", err)
		}

		// Break the loop if there are no more repositories
		if len(repositories) == 0 {
			break
		}

		if page > 1000050 {
			break
		}
		// Append retrieved repositories to the main slice
		allRepositories = append(allRepositories, repositories...)

		// Check if the slice is not empty
		// Check if the slice is not empty

		// Save the current page to resume later
		state.LastPage = page
		if err := SaveState(state); err != nil {
			log.Fatalf("Error saving state: %v", err)
		}

		// Move to the next page
		page++
	}

	if len(allRepositories) > 0 {
		// Print the first repository's ID and Name
		fmt.Printf("First Repository - ID: %d, Name: %s\n", allRepositories[0].ID, allRepositories[0].FullName)

		// Print the last repository's ID and Name
		fmt.Printf("Last Repository - ID: %d, Name: %s\n", allRepositories[len(allRepositories)-1].ID, allRepositories[len(allRepositories)-1].FullName)
	} else {
		fmt.Println("No repositories available.")
	}

	return allRepositories
}

func uploadToS3(s3Client *s3.S3, bucketName, key string, data []Repository) error {
	// Convert data to JSON
	jsonData, err := json.Marshal(data)
	if err != nil {
		return fmt.Errorf("failed to marshal data: %v", err)
	}

	// Upload JSON data as an S3 object
	_, err = s3Client.PutObject(&s3.PutObjectInput{
		Bucket:      aws.String(bucketName),
		Key:         aws.String(key),
		Body:        bytes.NewReader(jsonData),
		ContentType: aws.String("application/json"),
	})
	if err != nil {
		return fmt.Errorf("failed to upload data to S3: %v", err)
	}

	log.Printf("Successfully uploaded data to %s/%s\n", bucketName, key)
	return nil
}

func init() {
	// Explicitly load the .env file
	err := godotenv.Load("githubAccess.env")
	if err != nil {
		log.Fatalf("Error loading .env file: %v", err)
	}
}

func main() {
	bucketName := "cs547" // Replace with your S3 bucket name
	awsAccessKey := os.Getenv("AWS_ACCESS_KEY_ID")
	awsSecretKey := os.Getenv("AWS_SECRET_ACCESS_KEY")
	githubApiKey := os.Getenv("GITHUB_API_KEY")

	fmt.Println("AWS Access Key:", awsAccessKey)
	fmt.Println("AWS Secret Key:", awsSecretKey)
	fmt.Println("GitHub API Key:", githubApiKey)
	s3Client := createS3Client()

	// Fetch data from GitHub API
	data := fetchRepositories()

	// Define S3 object key with timestamp for uniqueness
	key := fmt.Sprintf("github_data_%s.json", time.Now().Format("20060102_150405"))

	// Upload data to S3
	if err := uploadToS3(s3Client, bucketName, key, data); err != nil {
		log.Fatalf("Error uploading to S3: %v", err)
	}
}
