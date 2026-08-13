-- CreateTable
CREATE TABLE "Report" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "threadId" TEXT NOT NULL,
    "topic" TEXT NOT NULL,
    "draft" TEXT NOT NULL,
    "wordCount" INTEGER NOT NULL,
    "revisionCount" INTEGER NOT NULL,
    "sources" TEXT NOT NULL,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- CreateIndex
CREATE UNIQUE INDEX "Report_threadId_key" ON "Report"("threadId");
