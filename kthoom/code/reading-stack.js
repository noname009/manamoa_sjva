/**
 * reading-stack.js
 *
 * Licensed under the MIT License
 *
 * Copyright(c) 2018 Google Inc.
 */
import { getElem } from './helpers.js';

// TODO: Have the ReadingStack subscribe to all of its book events.
// TODO: Have the ReadingStack display progress bars in the pane as books load
//       and unarchive.

/**
 * The ReadingStack is responsible for displaying information about the current
 * set of books the user has in their stack as well as the book they are
 * currently reading.  It also provides methods to add, remove and get a book.
 */
export class ReadingStack {
  constructor() {
    this.books_ = [];
    this.currentBookNum_ = -1;
    this.currentBookChangedCallbacks_ = [];

    getElem('readingStackTab')
        .addEventListener('click', () => this.toggleReadingStackOpen(), false);
  }

  getNumberOfBooks() { return this.books_.length; }

  getCurrentBook() {
    return this.currentBookNum_ != -1 ? this.books_[this.currentBookNum_] : null;
  }

  /** @param {number} i */
  getBook(i) {
    if (i < 0 || i >= this.books_.length) return null;
    return this.books_[i];
  }

  /**
   * Always changes to the newly added book.
   * @param {Book} book
   */
  addBook(book) {
    this.books_.push(book);
    //by soju
    //this.changeToBook_(this.books_.length - 1);
    this.renderStack_();
  }

  /**
   * @param {Array<Book>} books
   * @param {boolean} switchToFirst Whether to switch to the first book in this new set.
   */
  addBooks(books, switchToFirst) {
    //console.log('switchToFirst')
    if (books.length > 0) {
      const newCurrentBook = this.books_.length;
      for (const book of books) {
        this.books_.push(book);
      }
      if (switchToFirst) {
        this.changeToBook_(newCurrentBook);
      }
      this.renderStack_();
    }
  }

  /** @param {number} i */
  removeBook(i) {
    // Cannot remove the very last book.
    if (this.books_.length > 1 && i < this.books_.length) {
      this.books_.splice(i, 1);

      // If we are removing the book we are on, pick a new current book.
      if (i === this.currentBookNum_) {
        // Default to going to the next book unless we were on the last book
        // (in which case you go to the previous book).
        if (i >= this.books_.length) {
          i = this.books_.length - 1;
        }

        this.changeToBook_(i);
      } else {
        // Might have to update the current book number if the book removed
        // was above the current one.
        if (i < this.currentBookNum_) {
          this.currentBookNum_--;
        }
        this.renderStack_();
      }
    }
  }

  whenCurrentBookChanged(callback) {
    this.currentBookChangedCallbacks_.push(callback);
  }

  /** @return {boolean} */
  isOpen() {
    return getElem('readingStack').classList.contains('opened');
  }

  /**
   * Whether the reading stack is shown (if any books are loaded).
   * @return {boolean}
   */
  isShown() {
    return getElem('readingStack').style.visibility === 'visible';
  }

  /** @param {boolean} show */
  show(show) {
    getElem('readingStack').style.visibility = (show ? 'visible' : 'hidden');
  }

  changeToPrevBook() {
    if (this.currentBookNum_ > 0) {
      this.changeToBook_(this.currentBookNum_ - 1);
    }
  }

  changeToNextBook() {
    if (this.currentBookNum_ < this.books_.length - 1) {
      this.changeToBook_(this.currentBookNum_ + 1);
    }
  }

  changeToBook(i) {
    this.changeToBook_(i);
  }

  /**
   * @param {number} i
   * @private
   */
  changeToBook_(i) {
    if (i >= 0 && i < this.books_.length) {
      this.currentBookNum_ = i;
      const book = this.books_[i];
      for (const callback of this.currentBookChangedCallbacks_) {
        callback(book);
      }
      // Re-render to update selected highlight.
      this.renderStack_();
    }
  }

  toggleReadingStackOpen() {
    getElem('readingStack').classList.toggle('opened');
  }

  // TODO: Do this better so that each change of state doesn't require a complete re-render?
  /** @private */
  renderStack_() {
    const libDiv = getElem('readingStackContents');
    // Clear out the current reading stack HTML divs.
    libDiv.innerHTML = '';
    if (this.books_.length > 0) {
      for (let i = 0; i < this.books_.length; ++i) {
        const book = this.books_[i];
        const bookDiv = document.createElement('div');
        bookDiv.classList.add('readingStackBook');
        bookDiv.setAttribute('draggable', 'true');
        bookDiv.addEventListener('dragstart', evt => {
          evt.currentTarget.classList.add('dragging');
        });
        bookDiv.addEventListener('dragend', evt => {
          debugger;
          evt.currentTarget.classList.remove('dragging');
        });
        if (this.currentBookNum_ == i) {
          bookDiv.classList.add('current');
        }
        bookDiv.dataset.index = i;
        bookDiv.innerHTML =
            '<div class="readingStackBookInner" title="' + book.getName() + '">' +
              book.getName() +
            '</div>' +
            '<div class="readingStackBookCloseButton" title="Remove book from stack">x</div>';
        bookDiv.addEventListener('click', (evt) => {
          const i = parseInt(evt.currentTarget.dataset.index, 10);
          if (evt.target.classList.contains('readingStackBookCloseButton')) {
            this.removeBook(i);
          } else {
            this.changeToBook_(i);
          }
        });
        libDiv.appendChild(bookDiv);
      }
    }
  }
}
