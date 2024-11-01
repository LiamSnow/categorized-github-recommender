package main

import "time"

type Repository struct {
	ID               int       `json:"id"`
	FullName         string    `json:"full_name"`
	Fork             bool      `json:"fork,omitempty"`
	ForksCount       int       `json:"forks_count,omitempty"`
	StargazersCount  int       `json:"stargazers_count,omitempty"`
	SubscribersCount int       `json:"subscribers_count,omitempty"`
	Archived         bool      `json:"archived,omitempty"`
	Topics           []string  `json:"topics,omitempty"`
	CreatedAt        time.Time `json:"created_at,omitempty"`
	PushedAt         time.Time `json:"pushed_at,omitempty"`
	UpdatedAt        time.Time `json:"updated_at,omitempty"`
	Language         string    `json:"language,omitempty"`
}
