<template>
  <main>
    <div class="card mb-4 shadow-lg border border-secondary bg-dark text-light">
      <div class="card-body">
        <p class="card-text">{{ movie.left }} + {{ movie.right }} = {{ movie.sum }}</p>
        <div class="">
          <div class="d-flex justify-content-between align-items-center">
            <div class="btn-group">
              <button type="button" class="btn btn-sm btn-outline-secondary">
                <i class="fas fa-heart"></i>
              </button>
              <button type="button" class="btn btn-sm btn-outline-secondary" >
                <i class="fas fa-plus"></i>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </main>
</template>
<script>
export default {
  name: "AddCard",
  props: {
    movie: {
      type: Object,
      required: true,
    },
  },
};
</script>