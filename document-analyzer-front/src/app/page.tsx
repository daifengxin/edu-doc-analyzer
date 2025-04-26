"use client";

import { useState, FormEvent } from "react";

// Define interfaces for the API response
interface AnalysisScores {
  Clarity: number;
  Correctness: number;
  Completeness: number;
  Structure: number;
  Engagement: number;
}

interface AnalysisData {
  feedback: string;
  scores: AnalysisScores;
  overall_score: number;
  parsed_content?: string | null; // Optional field
}

interface ApiResponse {
  code: number;
  message: string;
  data: AnalysisData;
}

export default function Home() {
  const [file, setFile] = useState<File | null>(null);
  const [analysisResult, setAnalysisResult] = useState<AnalysisData | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files && event.target.files[0]) {
      setFile(event.target.files[0]);
      setAnalysisResult(null); // Clear previous results when a new file is selected
      setError(null); // Clear previous errors
    }
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!file) {
      setError("Please select a file first.");
      return;
    }

    setIsLoading(true);
    setError(null);
    setAnalysisResult(null);

    const formData = new FormData();
    formData.append("file", file);
    formData.append("filename", file.name);

    try {
      const response = await fetch("http://127.0.0.1:8000/v1/analyzer/document", { // Use the backend URL
        method: "POST",
        body: formData,
        // Headers are not explicitly set for FormData; the browser sets 'Content-Type': 'multipart/form-data' automatically.
      });

      if (!response.ok) {
        // Handle HTTP errors
        const errorData = await response.json().catch(() => ({ message: "Failed to parse error response." }));
        throw new Error(`API error: ${response.status} ${response.statusText}. ${errorData?.message || ''}`);
      }

      const result: ApiResponse = await response.json();

      if (result.code !== 200) {
        throw new Error(`API returned error code ${result.code}: ${result.message}`);
      }

      setAnalysisResult(result.data);

    } catch (err) {
      console.error("Error uploading or analyzing file:", err);
      setError(err instanceof Error ? err.message : "An unknown error occurred.");
    } finally {
      setIsLoading(false);
    }
  };


  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-8 bg-gray-50">
      <div className="w-full max-w-2xl bg-white p-8 rounded-lg shadow-md">
        <h1 className="text-2xl font-semibold mb-6 text-center text-gray-800">Document Analyzer</h1>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label htmlFor="file-upload" className="block text-sm font-medium text-gray-700 mb-2">
              Upload Document
            </label>
            <input
              id="file-upload"
              name="file-upload"
              type="file"
              onChange={handleFileChange}
              className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
              // Add accept attribute for specific file types if needed, e.g., accept=".docx,.pdf"
            />
          </div>

          <button
            type="submit"
            disabled={!file || isLoading}
            className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? "Analyzing..." : "Analyze Document"}
          </button>
        </form>

        {error && (
          <div className="mt-6 p-4 bg-red-100 border border-red-400 text-red-700 rounded">
            <p className="font-medium">Error:</p>
            <p>{error}</p>
          </div>
        )}

        {isLoading && (
           <div className="mt-6 text-center">
             <p className="text-gray-600">Loading analysis...</p>
             {/* Optional: Add a simple spinner */}
             <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto mt-2"></div>
           </div>
         )}


        {analysisResult && !isLoading && (
          <div className="mt-8 p-6 bg-gray-50 rounded-lg border border-gray-200">
            <h2 className="text-xl font-semibold mb-4 text-gray-700">Analysis Results</h2>

            <div className="mb-4">
              <h3 className="text-lg font-medium mb-2 text-gray-600">Overall Score:</h3>
              <p className="text-3xl font-bold text-blue-600">{analysisResult.overall_score.toFixed(1)}</p>
            </div>

            <div className="mb-4">
              <h3 className="text-lg font-medium mb-2 text-gray-600">Feedback:</h3>
              <p className="text-gray-800 whitespace-pre-wrap">{analysisResult.feedback}</p>
            </div>

            <div>
              <h3 className="text-lg font-medium mb-2 text-gray-600">Detailed Scores:</h3>
              <ul className="list-disc list-inside space-y-1 text-gray-800">
                {Object.entries(analysisResult.scores).map(([key, value]) => (
                  <li key={key}>
                    <span className="font-medium">{key}:</span> {value.toFixed(1)}
                  </li>
                ))}
              </ul>
            </div>

            {analysisResult.parsed_content && (
              <div className="mt-4">
                <h3 className="text-lg font-medium mb-2 text-gray-600">Parsed Content:</h3>
                <pre className="bg-white p-3 rounded border border-gray-300 text-sm overflow-auto">
                  <code>{analysisResult.parsed_content}</code>
                </pre>
               </div>
             )}
          </div>
        )}
      </div>
    </main>
  );
}
