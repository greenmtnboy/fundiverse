<template>
  <p class="demo">This is another component</p>
  <div v-for="d in data">{{ d }}</div>
</template>

<script>

export default {
  data() {
    return{
      data: [1,2,3]
    }
  }
}

</script>