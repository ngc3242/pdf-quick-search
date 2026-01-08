import { create } from 'zustand';
import type { Document, SearchResult } from '@/types';
import { documentApi, searchApi } from '@/api';

interface DocumentState {
  documents: Document[];
  total: number;
  page: number;
  perPage: number;
  pages: number;
  isLoading: boolean;
  error: string | null;

  // Search state
  searchQuery: string;
  searchResults: SearchResult[];
  searchTotal: number;
  isSearching: boolean;

  // Selected document for viewer
  selectedDocument: Document | null;

  // Actions
  fetchDocuments: (page?: number) => Promise<void>;
  uploadDocument: (file: File) => Promise<Document>;
  deleteDocument: (id: number) => Promise<void>;
  search: (query: string) => Promise<void>;
  clearSearch: () => void;
  setSelectedDocument: (doc: Document | null) => void;
  refreshDocument: (id: number) => Promise<void>;
}

export const useDocumentStore = create<DocumentState>((set, get) => ({
  documents: [],
  total: 0,
  page: 1,
  perPage: 20,
  pages: 0,
  isLoading: false,
  error: null,

  searchQuery: '',
  searchResults: [],
  searchTotal: 0,
  isSearching: false,

  selectedDocument: null,

  fetchDocuments: async (page = 1) => {
    set({ isLoading: true, error: null });
    try {
      const response = await documentApi.list(page, get().perPage);
      set({
        documents: response.documents,
        total: response.total,
        page: response.page,
        pages: response.pages,
        isLoading: false,
      });
    } catch (error: unknown) {
      const errorMessage =
        error instanceof Error ? error.message : '문서 목록을 불러오는데 실패했습니다';
      set({ error: errorMessage, isLoading: false });
    }
  },

  uploadDocument: async (file: File) => {
    set({ isLoading: true, error: null });
    try {
      const document = await documentApi.upload(file);
      // Refresh document list
      await get().fetchDocuments(get().page);
      return document;
    } catch (error: unknown) {
      const errorMessage =
        error instanceof Error ? error.message : '문서 업로드에 실패했습니다';
      set({ error: errorMessage, isLoading: false });
      throw error;
    }
  },

  deleteDocument: async (id: number) => {
    set({ isLoading: true, error: null });
    try {
      await documentApi.delete(id);
      // Refresh document list
      await get().fetchDocuments(get().page);
    } catch (error: unknown) {
      const errorMessage =
        error instanceof Error ? error.message : '문서 삭제에 실패했습니다';
      set({ error: errorMessage, isLoading: false });
      throw error;
    }
  },

  search: async (query: string) => {
    if (query.length < 2) {
      set({ searchQuery: '', searchResults: [], searchTotal: 0 });
      return;
    }

    set({ isSearching: true, searchQuery: query, error: null });
    try {
      const response = await searchApi.search(query);
      set({
        searchResults: response.results,
        searchTotal: response.total,
        isSearching: false,
      });
    } catch (error: unknown) {
      const errorMessage =
        error instanceof Error ? error.message : '검색에 실패했습니다';
      set({ error: errorMessage, isSearching: false });
    }
  },

  clearSearch: () => {
    set({ searchQuery: '', searchResults: [], searchTotal: 0 });
  },

  setSelectedDocument: (doc: Document | null) => {
    set({ selectedDocument: doc });
  },

  refreshDocument: async (id: number) => {
    try {
      const document = await documentApi.get(id);
      set((state) => ({
        documents: state.documents.map((doc) =>
          doc.id === id ? document : doc
        ),
        selectedDocument:
          state.selectedDocument?.id === id ? document : state.selectedDocument,
      }));
    } catch {
      // Ignore refresh errors
    }
  },
}));
